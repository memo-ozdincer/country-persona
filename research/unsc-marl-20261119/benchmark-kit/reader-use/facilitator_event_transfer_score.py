"""Grade new final records under frozen delivery and evidence-matched controls."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_event_transfer as study
import facilitator_bound_field_score as bound_score
import facilitator_fresh_brief_score as score


def readings(rows):
    result = {}
    for key, (quote, span, _, _) in study.opinions(rows).items():
        votes = []
        if quote != "unknown":
            for i, order in enumerate(study.judge.protocol.VIEWS):
                row = rows[f"{key}/judge{i}"]
                letter = row["output"]
                vote = study.judge.LABELS[order["ABC".index(letter)]] if row["ended"] and letter in ("A", "B", "C") else None
                votes.append(vote)
        agreement = quote if votes == [quote, quote] else "unknown"
        result[key] = {"quote": quote, "span": span, "judge": votes, "agreement": agreement}
    return result


def materials(rows):
    observed = readings(rows)
    cases = []
    for key, claim, truth, seen, receipts, _ in study.packets():
        panel, _ = key.rsplit("/", 1)
        relations = {mode: tuple(observed[f"{panel}/S{slot}"][mode] for slot in (1, 2))
                     for mode in ("quote", "agreement")}
        relations["oracle"] = truth
        actions = {mode: study.base.decision(values, seen) for mode, values in relations.items()}
        cases.append((key, claim, receipts, truth, seen, actions, relations))
    return observed, cases


def captured_fields(rows):
    return {k.removesuffix("/field"): v for k, v in rows.items() if k.endswith("/field")}


def captured_syntheses(rows):
    return {k: v for k, v in rows.items() if k.endswith(("/pooled", "/independent"))}


def replay(cases, policy, pooled, bound):
    modes = (
        ("full_access_pooled", None, None, "pooled"),
        ("same_receipts_pooled", "learned", "agreement", "pooled"),
        ("same_receipts_independent", "learned", "agreement", "independent"),
        ("quote_learned", "learned", "quote", "bound"),
        ("quote_erased", "learned_erased", "quote", "bound"),
        ("quote_greedy", "greedy", "quote", "bound"),
        ("agreement_learned", "learned", "agreement", "bound"),
        ("agreement_erased", "learned_erased", "agreement", "bound"),
        ("agreement_greedy", "greedy", "agreement", "bound"),
        ("oracle_learned", "learned", "oracle", "bound"),
    )
    by_panel = {}
    for case in cases:
        panel, _ = case[0].rsplit("/", 1)
        by_panel.setdefault(panel, {})[case[4]] = case
    base = study.base
    results = {}
    for inventory in ("overlap", "split"):
        results[inventory] = {}
        for arm, policy_name, relation, writer in modes:
            per_panel = {}
            for panel, packets in by_panel.items():
                _, _, _, truth, _, _, relations = packets[base.TARGETS]
                if policy_name:
                    stats, weights = base.distribution(policy_name, policy, base.base.roster(inventory), truth, relations[relation])
                else:
                    stats, weights = {"cost": 0.0}, {base.TARGETS: 1.0}
                value = Counter(send_cost=stats["cost"])
                for mask, weight in weights.items():
                    card, _, _, _, _, actions, _ = packets[mask]
                    if writer == "bound":
                        row = bound[f"{card}/{actions[relation]}"]
                    else:
                        name = f"{card}/{writer}"
                        row = pooled.get(name) or pooled[f"{card}/pooled"]
                    value["points"] += weight * row["points"]
                    value["false_action"] += weight * row["false_action"]
                    value["strict"] += weight * row["strict"]
                    for action in ("retain", "revise", "withhold"):
                        value[f"usable_{action}"] += weight * (row["strict"] and row["expected"] == action)
                value["net_actionable"] = value["usable_retain"] + value["usable_revise"] - value["false_action"] - value["send_cost"]
                per_panel[panel] = dict(value)
            keys = next(iter(per_panel.values())).keys()
            results[inventory][arm] = {"mean": {k: sum(d[k] for d in per_panel.values()) / len(per_panel) for k in keys},
                                       "panels": per_panel}
    return results


def run(directory, mode):
    rows = study.read(directory)
    pooled = captured_syntheses(rows)
    fields = captured_fields(rows)
    if mode == "review":
        inputs = score.review_inputs(pooled)
        for row in inputs:
            row.pop("independent_drafts", None)
        return inputs
    observed, cases = materials(rows)
    packet_sources = {k: v["sources"] for k, v in study.chair.load(study.PACK).items()}
    with (directory / "synthesis-review.tsv").open(newline="") as f:
        marks = list(csv.DictReader(f, delimiter="\t"))
    field_review = bound_score.semantic_review(directory, fields)
    with patch.object(study.chair, "fixtures", return_value=iter(cases)):
        pooled_grades = score.checks(pooled, marks)
    with patch.object(study.chair, "fixtures", side_effect=lambda: iter(cases)), \
         patch.object(study.chair.transfer, "packets", return_value=packet_sources):
        rendered, bound_grades = bound_score.render(fields, field_review)
    params = study.chair.transfer.policy(study.chair.transfer.FROZEN)
    totals = {}
    for kind, ends in (("field", ("/field",)), ("witness", ("/witness",)), ("judge", ("/judge0", "/judge1")),
                       ("pooled", ("/pooled",)), ("independent_synthesis", ("/independent",))):
        selected = [r for k, r in rows.items() if k.endswith(ends)]
        totals[kind] = {"calls": len(selected), "input_tokens": sum(len(r["input_ids"]) for r in selected),
                        "output_tokens": sum(len(r["output_ids"]) for r in selected)}
    return {"scope": "Two event-family transfer dockets with authored source cards and same-assistant semantic review. "
                     "The same final answer cap is used for pooled and independent syntheses. Recorded inference costs "
                     "are separate from simulated send costs. No policy updates.",
            "inference_totals": totals, "readings": observed, "syntheses": pooled_grades,
            "fields": field_review, "rendered": {k: v["output"] for k, v in sorted(rendered.items())},
            "bound_grades": dict(sorted(bound_grades.items())), "replay": replay(cases, params, pooled_grades, bound_grades),
            "review_sha256": {p: study.runner.digest(directory / p) for p in ("review.tsv", "synthesis-review.tsv")}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("review", "score"))
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.directory, args.mode), indent=2, ensure_ascii=False))
