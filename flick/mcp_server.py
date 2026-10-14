"""Minimal stdio MCP server. Tools call the phone. No screenshots, no secrets in logs."""
from __future__ import annotations

import json
import sys

from .loop import run_goal
from .phone import chrome, elements, status


def _tools() -> list[dict]:
    return [
        {
            "name": "phone_status",
            "description": "Is the plugged-in iPhone drivable? Call this before any other phone tool.",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "phone_see",
            "description": "Short labels on the current iPhone screen. Long private text is dropped.",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": "phone_goal",
            "description": "Give Clef or Jev a goal. They pick each tap from a closed list. Send, like, follow, and reply are refused.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "goal": {"type": "string"},
                    "steps": {"type": "integer", "minimum": 1, "maximum": 12},
                },
                "required": ["goal"],
            },
        },
    ]


def _handle(msg: dict) -> dict | None:
    method = msg.get("method")
    mid = msg.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": mid, "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "flick", "version": "0.1.0"},
        }}
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": mid, "result": {"tools": _tools()}}
    if method == "tools/call":
        name = (msg.get("params") or {}).get("name")
        args = (msg.get("params") or {}).get("arguments") or {}
        if name == "phone_status":
            st = status()
            text = json.dumps({k: st.get(k) for k in ("drivable", "device_state", "hint", "_ms")})
        elif name == "phone_see":
            ms, els = elements()
            text = json.dumps({"tree_ms": round(ms), "chrome": chrome(els)})
        elif name == "phone_goal":
            text = json.dumps(run_goal(args.get("goal") or "", int(args.get("steps") or 8)))
        else:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"unknown tool {name}"}}
        return {"jsonrpc": "2.0", "id": mid, "result": {"content": [{"type": "text", "text": text}]}}
    if mid is None:
        return None
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"unknown method {method}"}}


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        msg = json.loads(line)
        out = _handle(msg)
        if out is not None:
            sys.stdout.write(json.dumps(out) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
