"""Apply v1.5 quote validation and release scoring to the case's final verdicts."""
import argparse
import json
from pathlib import Path

import collect

HERE, e, CASE = collect.HERE, collect.e, collect.CASE


def run(marks_path):
    verified = e.read(HERE / "verified.json")
    marks = e.read(marks_path)
    assert set(marks) == set(verified["packets"])
    outcomes = {}
    for key, row in verified["traces"].items():
        calls = row["turns"]
        expected = e.judge.request(e.final_packet(CASE, calls))
        assert expected == verified["packets"][row["packet"]]
        score = e.final_score(CASE, calls, marks[row["packet"]])
        outcomes[key] = score | {"packet": row["packet"],
                                 "input_tokens": sum(c["input_tokens"] for c in calls),
                                 "output_tokens": sum(c["output_tokens"] for c in calls)}
    by_order = {}
    for order in (0, 1):
        arms = {arm: outcomes[f'{CASE["id"]}/{arm}/{order}'] for arm in e.ARMS}
        by_order[str(order)] = {
            f"peer_minus_{arm}": arms["peer"]["released_70"] - arms[arm]["released_70"]
            for arm in ("independent", "solo")
        }
    return {"scope": "one event and one assistant review", "paired_deltas": by_order,
            "results": outcomes, "sha256": {f.name: collect.pin(f) for f in
                                           (Path(__file__), marks_path, HERE / "verified.json")}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("marks", type=Path)
    e.emit(run(parser.parse_args().marks))
