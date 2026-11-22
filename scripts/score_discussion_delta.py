"""Replay matched revisions against both the solo revision and the common opening."""
import argparse
from collections import Counter
import json
from pathlib import Path


def transitions(opening, solo, peer):
    if not opening or opening.keys() != solo.keys() or solo.keys() != peer.keys():
        raise ValueError("Require identical nonempty criterion sets")
    counts = Counter()
    low = high = 0
    bounds = {"met": (1, 1), "unmet": (0, 0), "unratable": (0, 1)}
    for unit in solo:
        start, control, result = (arm[unit]["status"] for arm in (opening, solo, peer))
        low += bounds[result][0] - bounds[control][1]
        high += bounds[result][1] - bounds[control][0]
        if "unratable" in (control, result):
            counts["uncertain_pair"] += 1
        elif control == result:
            counts["stable_" + result] += 1
        elif result == "met":
            counts[{"met": "restored_opening", "unmet": "new_gain",
                    "unratable": "gain_origin_uncertain"}[start]] += 1
        else:
            counts["regression"] += 1
    return dict(counts=counts, units=len(solo), net_points_bounds=[low, high])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arm in ("opening", "solo", "peer"):
        parser.add_argument(arm, type=Path, help="manual-annotations.json for matched roles")
    args = parser.parse_args()
    arms = []
    for path in (args.opening, args.solo, args.peer):
        cases = json.loads(path.read_text())["cases"]
        indexed = {key.rsplit("-", 1)[0]: row for key, row in cases.items()}
        if len(indexed) != len(cases):
            raise ValueError("Ambiguous case identifiers")
        arms.append(indexed)
    if not arms[0] or any(arm.keys() != arms[0].keys() for arm in arms):
        raise ValueError("Require matching episode and role identifiers")
    report = {}
    for key in sorted(arms[0]):
        opening, solo, peer = (arm[key] for arm in arms)
        report[key] = transitions(opening["ratings"], solo["ratings"], peer["ratings"])
        report[key]["peer_engagement"] = peer["discussion_ratings"]["D2"]["status"]
        report[key]["peer_guards"] = {k: v["status"] for k, v in peer["universal_checks"].items()}
        report[key]["peer_content"] = {k: v["status"] for k, v in peer["ratings"].items()}
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
