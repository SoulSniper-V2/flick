"""Talk to a running iphone-use daemon. The phone does the work. This file does not."""
from __future__ import annotations

import json
import os
import plistlib
import time
import urllib.error
import urllib.request

BASE = os.environ.get("IPHONE_USE_URL", "http://127.0.0.1:44321")
PLIST = os.path.expanduser("~/Library/LaunchAgents/com.leeguoo.iphone-use.plist")


def token() -> str:
    if os.environ.get("IPHONE_USE_TOKEN"):
        return os.environ["IPHONE_USE_TOKEN"]
    with open(PLIST, "rb") as f:
        env = plistlib.load(f).get("EnvironmentVariables", {})
    return env.get("IPHONE_USE_AGENT_TOKEN") or env["IPHONE_USE_PASSWORD"]


def call(path: str, body: dict | None = None, timeout: float = 40) -> tuple[int, float, dict]:
    headers = {"Authorization": f"Bearer {token()}"}
    data = None
    if body is not None:
        headers["X-Phone-Control"] = "1"
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + path,
        data=data,
        headers=headers,
        method="POST" if body is not None else "GET",
    )
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


def status() -> dict:
    code, ms, body = call("/agent/status")
    body["_code"] = code
    body["_ms"] = round(ms)
    return body


def screen() -> tuple[float, str | None, list[dict]]:
    last = ""
    for _ in range(4):
        code, ms, body = call("/agent/elements", timeout=20)
        els = body.get("elements")
        if code == 200 and isinstance(els, list) and not body.get("error"):
            return ms, body.get("snapshot"), els
        last = str(body.get("error") or body)[:180]
        time.sleep(float(body.get("retry_after_secs") or 2))
    raise RuntimeError(last or "elements failed")


def elements() -> tuple[float, list[dict]]:
    ms, _, els = screen()
    return ms, els


def launch(name: str) -> tuple[int, float, dict]:
    return call("/agent/input", {"type": "launch_app", "app": name})


def home() -> tuple[int, float, dict]:
    return call("/agent/input", {"type": "shortcut", "name": "home"})


def chrome(els: list[dict], limit: int = 12) -> list[str]:
    out: list[str] = []
    for el in els:
        label = (el.get("label") or "").strip()
        if not label or len(label) > 28 or label in out:
            continue
        out.append(label)
        if len(out) >= limit:
            break
    return out


def has(els: list[dict], text: str) -> bool:
    needle = text.lower()
    return any(needle in (el.get("label") or "").lower() for el in els)
