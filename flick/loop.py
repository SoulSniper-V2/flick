"""One goal, many closed decisions. Clef and Jev pick. This file only executes."""
from __future__ import annotations

import time

from .decide import clef, denied, gate, jev
from .phone import chrome, elements, has, home, launch, call

SKIP = ("add", "compose", "edit", "remove", "more actions", "grok", "account menu", "profile photo")


def _skip(label: str) -> bool:
    low = label.lower()
    if denied(low):
        return True
    return any(word in low for word in SKIP)


def _candidates(els: list[dict]) -> list[tuple[str, str]]:
    """id, description. Ids are safe to send as choice keys."""
    in_x = any(el.get("kind") == "Application" and (el.get("label") or "") == "X" for el in els)
    out: list[tuple[str, str]] = [("done", "The comments on the /goal post are already on screen. Stop.")]
    if not in_x:
        out.append(("launch_x", "Open the X app by name. Do this first if X is not the foreground app."))
    out.append(("scroll_down", "Scroll down to reveal more of the current list."))
    out.append(("scroll_up", "Scroll up."))
    if in_x:
        out.append(("home", "Leave X only if you are stuck in the wrong screen."))
    if any(el.get("kind") == "SearchField" for el in els):
        out.append(("type_theo", "Type t3.gg into the search field and submit. Use this to find Theo."))
    labels: list[str] = []
    for el in els:
        label = (el.get("label") or "").strip().split("\n")[0]
        if not label or len(label) > 90 or label in labels or _skip(label):
            continue
        if el.get("kind") not in ("Button", "Cell", "Link", "SearchField", "Tab"):
            continue
        labels.append(label)
        if len(labels) >= 12:
            break
    # Search tab is the way into X search. Surface it even if it was past the cap.
    for el in els:
        label = (el.get("label") or "").strip()
        if "Search and Explore" in label and label not in labels:
            labels.insert(0, label)
    for i, label in enumerate(labels):
        out.append((f"tap_{i}", f"Tap: {label}"))
    return out


def _questions(cands: list[tuple[str, str]]) -> dict:
    return {
        "next": {
            "type": "choice",
            "instructions": "Pick the single next action that moves the goal forward. Do not follow, like, reply, or post.",
            "criteria": {key: desc for key, desc in cands},
        },
        "safe": {"type": "noul", "instructions": "This action does not send, post, like, follow, reply, or pay."},
        "kind": {
            "type": "choice",
            "instructions": "Classify the action.",
            "criteria": {"read": "Opening or reading", "send": "Sending or posting", "call": "Calling"},
        },
        "done": {"type": "noul", "instructions": "The comments on Theo's /goal post are already on screen."},
    }


def _execute(choice: str, cands: list[tuple[str, str]]) -> dict:
    desc = dict(cands).get(choice, "")
    if choice == "done":
        return {"action": "done"}
    if choice == "home":
        code, ms, body = home()
        return {"action": "home", "code": code, "ms": round(ms), "ok": body.get("ok")}
    if choice == "scroll_down":
        code, ms, body = call("/agent/input", {"type": "scroll", "x": 0.5, "y": 0.55, "dx": 0, "dy": 220})
        return {"action": "scroll_down", "code": code, "ms": round(ms)}
    if choice == "scroll_up":
        code, ms, body = call("/agent/input", {"type": "scroll", "x": 0.5, "y": 0.55, "dx": 0, "dy": -180})
        return {"action": "scroll_up", "code": code, "ms": round(ms)}
    if choice == "launch_x":
        code, ms, body = launch("X")
        return {"action": "launch_x", "code": code, "ms": round(ms), "ok": body.get("ok")}
    if choice == "type_theo":
        call("/agent/input", {"type": "text", "text": "t3.gg"})
        time.sleep(0.2)
        code, ms, body = call("/agent/input", {"type": "key", "name": "return"})
        return {"action": "type_theo", "code": code, "ms": round(ms)}
    if choice.startswith("tap_"):
        label = desc.removeprefix("Tap the control labeled: ")
        code, ms, body = call("/agent/input", {"type": "tap", "label": label})
        return {"action": choice, "label": label[:80], "code": code, "ms": round(ms), "ok": body.get("ok"), "error": body.get("error")}
    return {"action": choice, "skipped": True}


def run_goal(goal: str, steps: int = 10) -> dict:
    log = []
    # Constraints like "do not reply" are not requests. Only chosen actions are denied.
    for n in range(steps):
        tree_ms, els = elements()
        cands = _candidates(els)
        state = {
            "goal": goal,
            "chrome": chrome(els, 18),
            "comments_open": has(els, "Post your reply") or has(els, "Relevant"),
        }
        if state["comments_open"] and has(els, "Forgot to mention"):
            log.append({"step": n, "done": True, "why": "comments visible"})
            break
        questions = _questions(cands)
        vote = jev(state, questions)
        if vote.get("skip") or not vote.get("answers"):
            vote = clef("clef-omni", state, questions)
        ok, why = gate(vote.get("answers"))
        choice = ((vote.get("answers") or {}).get("next") or {}).get("choice")
        row = {
            "step": n,
            "tree_ms": round(tree_ms),
            "model_ms": vote.get("ms"),
            "model": vote.get("model") or "clef-omni",
            "choice": choice,
            "act": ok,
            "why": why,
            "chrome": state["chrome"][:8],
        }
        if not ok or not choice:
            row["stopped"] = True
            log.append(row)
            break
        if denied(choice) or denied(dict(cands).get(choice, "")):
            row["stopped"] = True
            row["why"] = "deny list"
            log.append(row)
            break
        row["did"] = _execute(choice, cands)
        log.append(row)
        if choice == "done":
            break
        time.sleep(0.45)
    _, els = elements()
    return {
        "goal": goal,
        "log": log,
        "comments_open": has(els, "Post your reply") or has(els, "Relevant"),
        "post_open": has(els, "Forgot to mention"),
        "photos": 0,
    }
