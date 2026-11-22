"""Compare all frozen conditions after validating every transcript and verdict."""
import argparse
from collections import defaultdict
from pathlib import Path
from statistics import mean

import evaluate as e


def load(path):
    if path.suffix == ".jsonl":
        return [e.json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return e.read(path)


def validate_episodes(records):
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
    for key, row in rows.items():
        e.require(set(row) in ({"id", "calls"}, {"id", "calls", "final", "process"}), "Malformed episode")
        name, arm, order = key.split("/")
        e.require(len(e.validate_calls(cases[name], arm, int(order), row["calls"])) == 3,
                  "All three turns are required")
    return cases, rows


def run(records):
    cases, rows = validate_episodes(records)
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

    def pair(name, order, baseline):
        peer = scores[f"{name}/peer/{order}"]
        other = scores[f"{name}/{baseline}/{order}"]
        p_final, b_final = peer["final"], other["final"]
        raw_delta = p_final["raw_70"][0] - b_final["raw_70"][0]
        released_delta = p_final["released_70"] - b_final["released_70"]
        changes = [
            {"criterion": rule["id"], "weight": rule["weight"],
             "baseline": b_final["units"][rule["id"]], "peer": p_final["units"][rule["id"]]}
            for rule in cases[name]["rubric"]
            if b_final["units"][rule["id"]] != p_final["units"][rule["id"]]
        ]
        return {
            "released_70": released_delta,
            "raw_lower_70": raw_delta,
            "release_gate_adjustment_70": released_delta - raw_delta,
            "baseline_release_blockers": b_final["release_blockers"],
            "peer_release_blockers": p_final["release_blockers"],
            "criterion_changes": changes,
            "input_tokens": peer["process"]["input_tokens"] - other["process"]["input_tokens"],
            "output_tokens": peer["process"]["output_tokens"] - other["process"]["output_tokens"],
        }

    pairs = {
        f"{name}/{order}": {baseline: pair(name, order, baseline)
                            for baseline in ("independent", "solo")}
        for name in cases for order in (0, 1)
    }

    tracked = {}
    for (track, family), names in sorted(families.items()):
        group = tracked.setdefault(track, {"families": {}})["families"]
        group[family] = {
            "cases": names,
            "peer_minus_independent_by_order": {
                str(order): mean(pairs[f"{name}/{order}"]["independent"]["released_70"] for name in names)
                for order in (0, 1)
            },
            "peer_minus_solo_by_order": {
                str(order): mean(pairs[f"{name}/{order}"]["solo"]["released_70"] for name in names)
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
                "points_10": mean(r["process"]["process_30"]["points"] for r in items),
                "arguments_10": mean(r["process"]["process_30"]["arguments"] for r in items),
                "completed_note_turns": mean(r["process"]["completed_note_turns"] for r in items),
                "unique_ideas": mean(r["process"]["unique_ideas"] for r in items),
                "supported_note_ideas_retained": mean(r["process"]["supported_note_ideas_retained"] for r in items),
                "unsupported_ideas_in_final": mean(r["process"]["unsupported_ideas_in_final"] for r in items),
                "cap_hits": mean(r["process"]["cap_hits"] for r in items),
                "errors": mean(r["process"]["errors"] for r in items),
                "input_tokens": mean(r["process"]["input_tokens"] for r in items),
                "output_tokens": mean(r["process"]["output_tokens"] for r in items),
            }
            if arm == "peer":
                stats["interactions_10"] = mean(r["process"]["process_30"]["interactions"] for r in items)
            if track == "workshop":
                stats["mechanical_accuracy"] = mean(r["mechanical"]["accepted"] for r in finals)
                for label, impasse in (("agreement", False), ("impasse", True)):
                    eligible = [scores[f"{name}/{arm}/{order}"]["final"]["mechanical"]["accepted"]
                                for name in names if (cases[name]["gold"] == ["IMPASSE"]) == impasse
                                for order in (0, 1)]
                    e.require(eligible, "Workshop family must include agreement and impasse")
                    stats[f"{label}_recall"] = mean(eligible)
                stats["balanced_accuracy"] = mean((stats["agreement_recall"], stats["impasse_recall"]))
            group[family]["arms"][arm] = stats

    for track in tracked.values():
        groups = list(track["families"].values())
        track["macro"] = {
            arm: {metric: mean(g["arms"][arm][metric] for g in groups)
                  for metric in groups[0]["arms"][arm]}
            for arm in e.ARMS
        }
        for baseline in ("independent", "solo"):
            metric = f"peer_minus_{baseline}_by_order"
            track[f"peer_minus_{baseline}_macro_by_order"] = {
                str(order): mean(g[metric][str(order)] for g in groups) for order in (0, 1)
            }
            track[f"peer_minus_{baseline}_macro"] = mean(
                track[f"peer_minus_{baseline}_macro_by_order"].values())
            family_effects = {
                family: mean(group[metric].values())
                for family, group in track["families"].items()
            }
            track[f"peer_minus_{baseline}_leave_one_family_out"] = {
                omitted: mean(effect for family, effect in family_effects.items() if family != omitted)
                for omitted in family_effects
            } if len(family_effects) > 1 else {}
            track[f"order_robust_family_wins_over_{baseline}"] = sum(
                all(d > 0 for d in g[metric].values()) for g in groups
            )
    return {"tracks": tracked, "paired_deltas": pairs, "episodes": scores,
            "cases": len(cases), "scored": len(scores)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("records", type=Path)
    e.emit(run(load(parser.parse_args().records)))
