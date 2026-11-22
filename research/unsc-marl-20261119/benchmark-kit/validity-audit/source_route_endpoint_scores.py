"""Score source-grounded endpoint records, then replay each routing arm."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from statistics import mean

from source_route_endpoint import label, traces
from source_route_memo_review import assess, bundle

WEIGHTS = {"P1": 4, "P2": 4, "C1": 7}


def score(directory, annotations):
    checked = assess(directory, annotations)
    _, join = bundle(directory)
    raw = {row["id"]: row for row in map(json.loads, (directory / "transcript.jsonl").read_text().splitlines())}
    packets = {}
    for key, ident in join.items():
        mark = checked["records"][ident]
        units = annotations["reviews"][key]["units"]
        packets[ident.split("/")[-2]] = {
            **mark, "met_units": [unit for unit, result in units.items() if result[0] == "met"],
            "completion_tokens": len(raw[ident]["output_ids"]), "ended": raw[ident]["ended"],
            "weighted_routing_realized": sum(points for unit, points in WEIGHTS.items() if units[unit][0] == "met"),
        }
    arms = {}
    for arm, rows in traces().items():
        worlds = [{**row, "packet": label(row["evidence"])} for row in rows]
        scores = [packets[world["packet"]] for world in worlds]
        arms[arm] = {
            "worlds": worlds,
            "mean_verified_record_points": mean(item["floor"] for item in scores),
            "mean_record_ceiling": mean(item["ceiling"] for item in scores),
            "mean_weighted_routing_realized": mean(item["weighted_routing_realized"] for item in scores),
            "critical_failures": sum(item["critical_guard"] == "failed" for item in scores),
            "uncertain_guards": sum(item["critical_guard"] == "uncertain" for item in scores),
            "over_limit": sum(not item["under_limit"] for item in scores),
            "capped": sum(not item["ended"] for item in scores),
            "positions_and_comparison_counts": {unit: sum(unit in item["met_units"] for item in scores) for unit in WEIGHTS},
            "mean_simulator_return": mean(world["return"] for world in worlds),
        }
    return {"scope": annotations["scope"], "transcript_sha256": checked["transcript_sha256"],
            "annotations_sha256": sha256((directory / "annotations.json").read_bytes()).hexdigest(),
            "packets": packets, "arms": arms}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--score", action="store_true")
    args = parser.parse_args()
    if args.score:
        annotations = json.loads((args.directory / "annotations.json").read_text())
        result = score(args.directory, annotations)
    else:
        result = bundle(args.directory)[0]
    print(json.dumps(result, ensure_ascii=False, indent=2))
