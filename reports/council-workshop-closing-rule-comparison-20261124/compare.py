"""Measure the closing rule on a frozen snapshot of registered decisions."""

import argparse
import json
from pathlib import Path
from runpy import run_path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research/council_workshop"))

from held_suite import SOL, score
from run import pretty
from scorecard import endpoint, registered_paths


def capture():
    return [path.relative_to(ROOT).as_posix() for path in registered_paths()]


def compare(paths):
    settings = {path: json.loads((path / "settings.json").read_text()) for path in paths}
    registered = score(paths)
    moderator = HERE.parent / "council-workshop-moderator-certificate-20261123" / "replay-stop.py"
    replay_stop = run_path(str(moderator))["compare"]
    rows = []
    for path, setup in settings.items():
        if not (path / "result.json").is_file():
            continue
        replayed = replay_stop(path, setup)
        arm = "sol-with-focus-swap" if setup.get("seat_models") else "all-sol"
        assert setup["model"] == SOL
        original = endpoint(replayed["original"])
        automatic = endpoint(replayed["automatic"])
        rows.append({
            "family": replayed["family"], "world": replayed["world"], "opener": replayed["order"][0],
            "arm": arm, "original": original, "automatic": automatic,
            "moderator_closed": replayed["automatic_certificate"], "path": path.relative_to(ROOT).as_posix(),
        })
    assert len(rows) == sum(registered["completed_by_arm"].values())
    by_cell = {(r["family"], r["world"], r["opener"], r["arm"]): r for r in rows}
    matches = []
    for pair in registered["matched_focus_swaps"]:
        key = pair["family"], pair["world"], pair["opener"]
        baseline = by_cell[(*key, pair["baseline"])]
        mixed = by_cell[(*key, pair["arm"])]
        deltas = {rule: mixed[rule]["reward"] - baseline[rule]["reward"] for rule in ("original", "automatic")}
        assert deltas["original"] == pair["reward_delta"]
        matches.append({"family": key[0], "world": key[1], "opener": key[2], "reward_delta": deltas})

    return {
        "completed": len(rows), "interrupted": sum(registered.get("aborted_by_arm", {}).values()),
        "successes": {rule: sum(row[rule]["reward"] for row in rows) for rule in ("original", "automatic")},
        "calls_saved": sum(row["original"]["calls"] - row["automatic"]["calls"] for row in rows),
        "matches": matches, "meetings": rows,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture-paths", action="store_true")
    args = parser.parse_args()
    if args.capture_paths:
        print(pretty(capture()))
    else:
        paths = [ROOT / path for path in json.loads((HERE / "paths.json").read_text())]
        print(pretty(compare(paths)))
