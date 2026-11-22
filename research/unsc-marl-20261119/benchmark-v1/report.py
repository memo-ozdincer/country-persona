"""Compare all frozen conditions after validating every transcript and verdict."""
import argparse
from collections import defaultdict
from pathlib import Path
from statistics import mean

import evaluate as e


def run(records):
    cases = e.cases()
    rows = e.judge.by_id(records)
    expected = {f"{case}/{arm}/{order}" for case in cases for arm in e.ARMS for order in (0, 1)}
    e.require(set(rows) == expected, "All cases, arms and both speaker orders are required")
    for name in cases:
        for order in (0, 1):
            peer = rows[f"{name}/peer/{order}"]["calls"]
            independent = rows[f"{name}/independent/{order}"]["calls"]
            e.require(peer and independent and
                      {k: v for k, v in peer[0].items() if k != "request_sha256"} ==
                      {k: v for k, v in independent[0].items() if k != "request_sha256"},
                      "Paired runs must share their opening note and token counts")
    scores = {}
    for key, row in rows.items():
        e.require(set(row) == {"id", "calls", "final", "process"}, "Malformed comparison record")
        name, arm, order = key.split("/")
        case = cases[name]
        calls = e.validate_calls(case, arm, int(order), row["calls"])
        scores[key] = {
            "final": e.final_score(case, calls, row["final"]),
            "process": e.process_score(case, calls, row["process"]),
        }
    families = defaultdict(list)
    for name, case in cases.items():
        families[case["track"], case["family"]].append(name)

    def paired_delta(name, order, baseline):
        peer = scores[f"{name}/peer/{order}"]["final"]["released_70"]
        other = scores[f"{name}/{baseline}/{order}"]["final"]["released_70"]
        return peer - other

    tracked = {}
    for (track, family), names in sorted(families.items()):
        group = tracked.setdefault(track, {"families": {}})["families"]
        group[family] = {
            "cases": names,
            "peer_minus_independent_by_order": {
                str(order): mean(paired_delta(name, order, "independent") for name in names)
                for order in (0, 1)
            },
            "peer_minus_solo_by_order": {
                str(order): mean(paired_delta(name, order, "solo") for name in names)
                for order in (0, 1)
            },
            "arms": {},
        }
        for arm in e.ARMS:
            items = [scores[f"{name}/{arm}/{order}"] for name in names for order in (0, 1)]
            finals = [item["final"] for item in items]
            stats = {
                "released_70": mean(r["released_70"] for r in finals),
                "raw_lower_70": mean(r["raw_70"][0] for r in finals),
                "raw_upper_70": mean(r["raw_70"][1] for r in finals),
                "release_rate": mean(r["release"] for r in finals),
                "strict_rate": mean(r["strict"] for r in finals),
                "input_tokens": mean(r["process"]["input_tokens"] for r in items),
                "output_tokens": mean(r["process"]["output_tokens"] for r in items),
            }
            if track == "workshop":
                stats["mechanical_accuracy"] = mean(r["mechanical"]["accepted"] for r in finals)
                for label, impasse in (("agreement", False), ("impasse", True)):
                    eligible = [scores[f"{name}/{arm}/{order}"]["final"]["mechanical"]["accepted"]
                                for name in names if (cases[name]["gold"] == ["IMPASSE"]) == impasse
                                for order in (0, 1)]
                    e.require(eligible, "Workshop family must include agreement and impasse")
                    stats[f"{label}_recall"] = mean(eligible)
            group[family]["arms"][arm] = stats

    for track in tracked.values():
        groups = list(track["families"].values())
        track["macro"] = {
            arm: {metric: mean(g["arms"][arm][metric] for g in groups)
                  for metric in groups[0]["arms"][arm]}
            for arm in e.ARMS
        }
        track["order_robust_family_wins_over_independent"] = sum(
            all(d > 0 for d in g["peer_minus_independent_by_order"].values()) for g in groups
        )
    return {"tracks": tracked, "episodes": scores, "cases": len(cases), "scored": len(scores)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", type=Path)
    e.emit(run(e.read(parser.parse_args().records)))
