"""Clef and Jev. Closed questions only. Jev sees images when the danger-zone header is set."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

CF_ACCOUNT = os.environ.get("CF_ACCOUNT", "")
CF_TOKEN = os.environ.get("CF_TOKEN") or os.environ.get("CLOUDFLARE_API_TOKEN", "")
JEV_KEY = os.environ.get("JEV_KEY") or os.environ.get("TYPESAFE_API_KEY", "")
FLOOR = 0.72

DENY = (
    "send", "reply", "repost", "retweet", "post", "tweet", "like", "follow",
    "unfollow", "call", "pay", "buy", "purchase", "subscribe", "delete", "compose",
)


def denied(text: str) -> str | None:
    low = (text or "").lower()
    for word in DENY:
        if word in low:
            return word
    return None


def _post(url: str, headers: dict, body: dict, timeout: float = 45) -> tuple[int, float, dict]:
    import time
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method="POST")
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, (time.perf_counter() - t0) * 1000, json.loads(resp.read())
    except urllib.error.HTTPError as err:
        raw = err.read().decode()[:400]
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"error": raw}
        return err.code, (time.perf_counter() - t0) * 1000, parsed


def jev(state, questions: dict, assets: dict | None = None) -> dict:
    if not JEV_KEY:
        return {"skip": "JEV_KEY unset"}
    body = {"model": "jev-latest", "state": state, "questions": questions}
    headers = {
        "Authorization": f"Bearer {JEV_KEY}",
        "Content-Type": "application/json",
    }
    if assets:
        body["assets"] = assets
        headers["TypeSafe-Danger-Zone-Images"] = "true"
    code, ms, parsed = _post("https://api.typesafe.ai/v1/systemone", headers, body)
    return {
        "code": code,
        "ms": round(ms),
        "model": parsed.get("model") if isinstance(parsed, dict) else None,
        "answers": parsed.get("answers") if isinstance(parsed, dict) else None,
        "error": parsed.get("error") if isinstance(parsed, dict) else parsed,
    }


def clef(selector: str, state, questions: dict, images: list[str] | None = None) -> dict:
    if not CF_ACCOUNT or not CF_TOKEN:
        return {"skip": "CF_ACCOUNT or CF_TOKEN unset"}
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT}/ai/run/@cf/cloudflare/{selector}"
    body = {"model": selector, "state": state, "questions": questions}
    if images:
        body["images"] = images
    code, ms, parsed = _post(
        url,
        {"Authorization": f"Bearer {CF_TOKEN}", "Content-Type": "application/json"},
        body,
        timeout=60,
    )
    result = parsed.get("result", parsed) if isinstance(parsed, dict) else {}
    return {
        "code": code,
        "ms": round(ms),
        "answers": (result or {}).get("answers") if isinstance(result, dict) else None,
        "error": parsed.get("error") if isinstance(parsed, dict) else None,
    }


def gate(answers: dict | None) -> tuple[bool, str]:
    if not answers:
        return False, "no answers"
    kind = ((answers.get("kind") or {}).get("choice"))
    safe = ((answers.get("safe") or {}).get("noul"))
    if kind in ("send", "pay", "call", "delete"):
        return False, f"kind={kind}"
    if safe is None:
        return False, "no safety score"
    if safe < FLOOR:
        return False, f"safe={safe:.2f}<{FLOOR}"
    return True, f"safe={safe:.2f}"
