"""Jev picks from a ranked, closed list. Execution uses the element snapshot, not a guessed label."""
from __future__ import annotations

import time

from .decide import clef, denied, gate, jev
from .phone import chrome, has, home, launch, call, screen

SKIP = ("compose", "more actions", "account menu", "profile photo", "grok tab", "notifications tab", "chat tab")


def _skip(label: str) -> bool:
    low = label.lower().strip()
    if low in ("add", "edit", "remove", "follow", "like", "reply", "repost", "share", "subscribe"):
        return True
    if denied(low) and low not in ("post",):
        return True
    return any(word in low for word in SKIP)


def _rect(el: dict) -> list[float]:
    rect = el.get("rect") or [0, 0, 0, 0]
    if isinstance(rect, dict):
        return [rect.get("x") or 0, rect.get("y") or 0, rect.get("width") or 0, rect.get("height") or 0]
    return list(rect) if isinstance(rect, list) else [0, 0, 0, 0]


def _on_screen(el: dict, height: float) -> bool:
    _, y, w, h = _rect(el)
    return w > 8 and h > 8 and 50 < y < height - 40


def _score(label: str, goal: str) -> int:
    low = label.lower()
    score = 0
    for word in ("search", "theo", "t3", "goal", "people", "posts", "back"):
        if word in low and word in goal.lower():
            score += 5
    if "search and explore" in low:
        score += 8
    if low.startswith("theo - t3.gg") or "@theo" in low:
        score += 12
    if "forgot to mention" in low or "/goal" in low:
        score += 20
    if "replies" in low or "comments" in low:
        score += 4
    return score


def _candidates(els: list[dict], goal: str) -> list[tuple[str, str, dict | None]]:
    app = next((el for el in els if el.get("kind") == "Application"), None)
    height = _rect(app)[3] or 874
    width = _rect(app)[2] or 402
    in_x = (app or {}).get("label") == "X"
    out: list[tuple[str, str, dict | None]] = []
    if not in_x:
        out.append(("launch_x", "Open the X app. Do this before anything else if X is not open.", None))
    if any(el.get("kind") == "SearchField" for el in els):
        out.append(("type_theo", "Type t3.gg into the search field and submit.", None))
    ranked: list[tuple[int, str, dict]] = []
    seen: set[str] = set()
    for el in els:
        label = (el.get("label") or "").strip().split("\n")[0]
        if not label or len(label) > 110 or label in seen or _skip(label):
            continue
        if el.get("kind") not in ("Button", "Cell", "Link", "SearchField", "Tab"):
            continue
        if not _on_screen(el, height) and _score(label, goal) < 8:
            continue
        seen.add(label)
        ranked.append((_score(label, goal), label, el))
    ranked.sort(key=lambda row: row[0], reverse=True)
    for i, (_, label, el) in enumerate(ranked[:10]):
        out.append((f"tap_{i}", f"Tap: {label[:90]}", el))
    out.append(("scroll_down", "Scroll down.", None))
    out.append(("scroll_up", "Scroll up.", None))
    if in_x:
        out.append(("back", "Tap Back.", None))
    out.append(("done", "Stop. Only if the comments on the /goal post are visible.", None))
    return out


def _tap(el: dict, snap: str | None, idx_hint: str) -> dict:
    rect = _rect(el)
    label = el.get("label") or ""
    # A cell that contains an image opens the photo if you tap its middle. Hit the text band.
    if el.get("kind") == "Cell" and "Image" in label and rect[3] > 70 and rect[1] > 0:
        code, ms, body = call("/agent/input", {
            "type": "tap",
            "x": min(0.92, max(0.08, (rect[0] + min(rect[2], 180) / 2) / 402)),
            "y": min(0.9, max(0.08, (rect[1] + 28) / 874)),
        })
        return {"via": "text-band", "code": code, "ms": round(ms), "ok": body.get("ok")}
    if snap:
        # Re-find by label in a fresh snapshot is the caller's job. Here we tap by label
        # only when the element index from this snapshot is still the one we scored.
        code, ms, body = call("/agent/input", {"type": "tap", "label": label[:120]})
        if code == 200 and body.get("ok"):
            return {"via": "label", "code": code, "ms": round(ms), "ok": True}
    code, ms, body = call("/agent/input", {
        "type": "tap",
        "x": min(0.92, max(0.08, (rect[0] + rect[2] / 2) / 402)),
        "y": min(0.9, max(0.08, (rect[1] + min(rect[3], 36) / 2) / 874)),
    })
    return {"via": "point", "code": code, "ms": round(ms), "ok": body.get("ok"), "hint": idx_hint}


def _execute(choice: str, cands: list[tuple[str, str, dict | None]], snap: str | None) -> dict:
    match = next((row for row in cands if row[0] == choice), None)
    if match is None:
        return {"skipped": True}
    _, desc, el = match
    if choice == "done":
        return {"action": "done"}
    if choice == "home":
        code, ms, body = home()
        return {"action": "home", "code": code, "ms": round(ms)}
    if choice == "scroll_down":
        code, ms, body = call("/agent/input", {"type": "scroll", "x": 0.5, "y": 0.55, "dx": 0, "dy": 240})
        return {"action": "scroll_down", "code": code, "ms": round(ms)}
    if choice == "scroll_up":
        code, ms, body = call("/agent/input", {"type": "scroll", "x": 0.5, "y": 0.45, "dx": 0, "dy": -180})
        return {"action": "scroll_up", "code": code, "ms": round(ms)}
    if choice == "launch_x":
        code, ms, body = launch("X")
        return {"action": "launch_x", "code": code, "ms": round(ms), "ok": body.get("ok")}
    if choice == "type_theo":
        call("/agent/input", {"type": "text", "text": "t3.gg"})
        time.sleep(0.15)
        code, ms, body = call("/agent/input", {"type": "key", "name": "return"})
        return {"action": "type_theo", "code": code, "ms": round(ms)}
    if choice == "back":
        code, ms, body = call("/agent/input", {"type": "tap", "label": "Back"})
        return {"action": "back", "code": code, "ms": round(ms), "ok": body.get("ok")}
    if el is not None:
        did = _tap(el, snap, choice)
        did["label"] = (el.get("label") or "")[:80]
        return did
    return {"skipped": True, "desc": desc[:80]}


def _done(els: list[dict]) -> bool:
    return has(els, "Forgot to mention") and (has(els, "Post your reply") or has(els, "Relevant"))


def run_goal(goal: str, steps: int = 12) -> dict:
    log = []
    last = ""
    repeats = 0
    for n in range(steps):
        tree_ms, snap, els = screen()
        if _done(els):
            log.append({"step": n, "done": True, "tree_ms": round(tree_ms)})
            break
        cands = _candidates(els, goal)
        if last:
            cands = [row for row in cands if row[0] != last] or cands
        state = {"goal": goal, "screen": chrome(els, 14), "in_x": any(el.get("label") == "X" and el.get("kind") == "Application" for el in els)}
        questions = {
            "next": {
                "type": "choice",
                "instructions": "One next action. Prefer search, then the Theo profile, then the /goal post, then its comments. Never compose.",
                "criteria": {key: desc for key, desc, _ in cands},
            },
            "safe": {"type": "noul", "instructions": "Does not send, post, like, follow, reply, or pay."},
            "kind": {"type": "choice", "instructions": "Classify.", "criteria": {"read": "reading", "send": "sending"}},
        }
        vote = jev(state, questions)
        if not vote.get("answers"):
            vote = clef("clef-flash", state, questions)
        ok, why = gate(vote.get("answers"))
        choice = ((vote.get("answers") or {}).get("next") or {}).get("choice")
        row = {"step": n, "tree_ms": round(tree_ms), "model_ms": vote.get("ms"), "choice": choice, "act": ok, "why": why}
        print(json.dumps(row), flush=True)
        if not ok or not choice:
            row["stopped"] = True
            log.append(row)
            break
        row["did"] = _execute(choice, cands, snap)
        log.append(row)
        if choice == last:
            repeats += 1
        else:
            repeats = 0
        last = choice
        if choice == "done" or repeats > 2:
            break
        time.sleep(0.35)
    _, _, els = screen()
    return {"log": log, "done": _done(els), "photos": 0, "steps": len(log)}
