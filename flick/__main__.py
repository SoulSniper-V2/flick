"""flick — open apps on a real iPhone and print how long it took. No screenshots."""
from __future__ import annotations

import argparse
import json
import sys
import time

from . import __version__
from .phone import chrome, elements, has, home, launch, status


def cmd_status() -> int:
    st = status()
    print(json.dumps({
        "drivable": st.get("drivable"),
        "state": st.get("device_state"),
        "hint": st.get("hint") or "",
        "ms": st.get("_ms"),
    }, indent=2))
    return 0 if st.get("drivable") else 1


def cmd_see() -> int:
    ms, els = elements()
    print(json.dumps({"tree_ms": round(ms), "n": len(els), "chrome": chrome(els)}, indent=2))
    return 0


def _open(name: str, marker: str) -> dict:
    t0 = time.perf_counter()
    code, launch_ms, body = launch(name)
    tree_ms = 0.0
    els: list[dict] = []
    deadline = time.perf_counter() + 3.0
    while time.perf_counter() < deadline:
        tree_ms, els = elements()
        if has(els, marker):
            break
        time.sleep(0.25)
    return {
        "app": name,
        "ok": code == 200 and bool(body.get("ok")) and has(els, marker),
        "launch_ms": round(launch_ms),
        "tree_ms": round(tree_ms),
        "wall_ms": round((time.perf_counter() - t0) * 1000),
        "marker": marker,
        "saw": has(els, marker),
        "error": body.get("error"),
    }


def cmd_demo() -> int:
    st = status()
    if not st.get("drivable"):
        print(json.dumps({"stopped": True, "why": st.get("hint") or st.get("device_state")}))
        return 1
    t0 = time.perf_counter()
    rows = [
        _open("Weather", "Weather"),
        _open("Clock", "Clock"),
        _open("Calendar", "Calendar"),
    ]
    home_code, home_ms, _ = home()
    total = round((time.perf_counter() - t0) * 1000)
    print(json.dumps({
        "steps": rows,
        "home_ms": round(home_ms),
        "home_ok": home_code == 200,
        "total_ms": total,
        "photos": 0,
    }, indent=2))
    return 0 if all(row["ok"] for row in rows) else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="flick")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status").set_defaults(fn=cmd_status)
    sub.add_parser("see").set_defaults(fn=cmd_see)
    sub.add_parser("demo").set_defaults(fn=cmd_demo)
    args = parser.parse_args(argv)
    return args.fn()


if __name__ == "__main__":
    sys.exit(main())
