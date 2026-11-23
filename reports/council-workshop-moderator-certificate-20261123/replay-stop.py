"""Replay recorded all-Sol prefixes with moderator certification enabled."""

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "research/council_workshop"))

from held_suite import SOL, identify, metrics
from recording import Recording, decision_request
from replay import replay
from run import pretty, simulate
from scorecard import registered_paths


def compare(directory, settings):
    family, world, _, order = identify(settings)
    original = replay(directory)
    recording = Recording(directory)

    def recorded(seat, prompt, schema):
        reply = recording.take(decision_request(settings, seat, prompt, schema))
        if reply is None:
            raise ValueError("Automatic closing reached a decision outside the archived prefix")
        return reply

    case = settings["case"]
    automatic = simulate(case, order, "meeting", settings["turn_cap"], settings["vote"], recorded,
                         call_cap=settings["call_cap"], auto_certify_impasse=True)
    assert automatic["history"] == original["history"][:len(automatic["history"])]
    assert automatic["calls"] <= original["calls"]
    if automatic.get("certificate_source") != "moderator":
        assert automatic == original
    return {"family": family, "world": world, "order": order,
            "original": metrics(original, case), "automatic": metrics(automatic, case),
            "automatic_certificate": automatic.get("certificate_source") == "moderator",
            "calls_saved": original["calls"] - automatic["calls"],
            "archived_path": str(directory.relative_to(HERE.parents[1]))}


if __name__ == "__main__":
    rows = []
    for trace in registered_paths():
        settings = json.loads((trace / "settings.json").read_text())
        if settings["model"] == SOL and not settings.get("seat_models"):
            rows.append(compare(trace, settings))
    assert len(rows) == 8 and len({(r["family"], r["world"], r["order"][0]) for r in rows}) == 8
    print(pretty({"meetings": rows, "new_successes": sum(r["automatic"]["reward"] - r["original"]["reward"] for r in rows),
                  "total_calls_saved": sum(r["calls_saved"] for r in rows)}))
