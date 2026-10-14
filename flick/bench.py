"""Time every decision model on one frozen screen. Does not touch the phone."""
from __future__ import annotations

import time

from .decide import clef, jev

STATE = {
    "goal": "Open Theo's /goal post on X and show the comments. Do not like or reply.",
    "screen": ["X", "Search and Explore tab", "For you", "Following", "Theo - t3.gg"],
    "in_x": True,
}
QUESTIONS = {
    "next": {
        "type": "choice",
        "instructions": "One next action. Prefer search, then Theo, then the post. Never compose.",
        "criteria": {
            "tap_search": "Tap Search and Explore",
            "type_theo": "Type t3.gg in the search field",
            "tap_theo": "Tap Theo - t3.gg",
            "scroll_down": "Scroll down",
            "home": "Go home",
        },
    },
    "safe": {"type": "noul", "instructions": "Does not send, like, follow, or reply."},
}


def run() -> list[dict]:
    rows = []
    calls = [
        ("jev", lambda: jev(STATE, QUESTIONS)),
        ("clef-flash", lambda: clef("clef-flash", STATE, QUESTIONS)),
        ("clef", lambda: clef("clef", STATE, QUESTIONS)),
        ("clef-omni", lambda: clef("clef-omni", STATE, QUESTIONS)),
    ]
    for name, fn in calls:
        t0 = time.perf_counter()
        result = fn()
        answers = result.get("answers") or {}
        rows.append({
            "model": name,
            "ms": result.get("ms") or round((time.perf_counter() - t0) * 1000),
            "choice": (answers.get("next") or {}).get("choice"),
            "safe": (answers.get("safe") or {}).get("noul"),
            "code": result.get("code"),
            "error": result.get("error") if not answers else None,
        })
    return rows
