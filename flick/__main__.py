"""flick — Clef or Jev pick the taps. No screenshot per step."""
from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .loop import run_goal
from .phone import chrome, elements, status


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


def cmd_goal(goal: str, steps: int) -> int:
    print(json.dumps(run_goal(goal, steps), indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="flick")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status").set_defaults(fn=lambda a: cmd_status())
    sub.add_parser("see").set_defaults(fn=lambda a: cmd_see())
    g = sub.add_parser("goal")
    g.add_argument("goal")
    g.add_argument("--steps", type=int, default=8)
    g.set_defaults(fn=lambda a: cmd_goal(a.goal, a.steps))
    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
