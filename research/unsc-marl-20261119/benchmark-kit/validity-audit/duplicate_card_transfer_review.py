"""Evaluate the frozen DPRK transfer with guarded component-level provenance."""
import argparse
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

from duplicate_card_hybrid import cited_ids
from duplicate_card_routes import exact
from duplicate_card_transfer import CASE, suite
from duplicate_card_transfer_routes import run as replay_routes
import source_record_review as reviewer


def load(directory):
    rows = [json.loads(line) for line in (directory / "transcript.jsonl").read_text().splitlines()]
    case = json.loads(CASE.read_text())
    labels = {name: entry["criterion"] for name, entry in case["cards"].items()}
    deck, parts = {}, {}
    for expected, row in zip(suite(), rows, strict=True):
        assert all(row[k] == value for k, value in expected.items())
        name = row["id"].split("/")[-2]
        sources = json.loads(row["messages"][-1]["content"])["evidence"]
        criteria = {k: v for k, v in case["criteria"].items()
                    if (k not in labels.values() if name == "public" else k == labels[name])}
        deck[name] = {"criteria": criteria, "evidence": sources, "candidate": row["output"]}
        parts[name] = row
    return case, labels, deck, parts


def review(directory):
    case, labels, deck, parts = load(directory)
    annotations_path = directory / "annotations.json"
    annotations = json.loads(annotations_path.read_text())
    with patch.object(reviewer, "bundle", return_value=(deck, {name: name for name in deck})):
        parts_scores = reviewer.score(directory, annotations)
    routes = replay_routes()
    slots = (None, *routes["slots"])
    ratings = {}
    for count in range(3):
        for receipt in combinations(routes["slots"], count):
            key = frozenset(receipt)
            roles = [name for name in receipt if parts_scores[name]["floor"] == 7 and
                     parts_scores[name]["critical_guard"] == "clear" and parts[name]["ended"] and
                     cited_ids(parts[name]["output"]) <= {name}]
            clauses = [parts[name]["output"] if name in cited_ids(parts[name]["output"])
                       else f"{parts[name]['output']} [{name}]" for name in roles]
            raw_record = "\n\n".join(parts[name]["output"] for name in ("public", *receipt))
            hybrid = "\n\n".join([case["public_reference"], *clauses, case["analysis"]])
            assert len(hybrid.split()) <= 160 and cited_ids(hybrid) == set(case["public"]) | set(roles)
            visible = set(case["public"]) | set(receipt)
            ratings[key] = {
                "received": receipt, "raw_record": raw_record,
                "raw_points": sum(parts_scores[name]["floor"] for name in ("public", *receipt)),
                "raw_unknown_citations": sorted(cited_ids(raw_record) - visible),
                "raw_missing_citations": sorted(visible - cited_ids(raw_record)),
                "raw_guard_by_component": {name: parts_scores[name]["critical_guard"] for name in ("public", *receipt)},
                "raw_words": len(raw_record.split()),
                "performed_components": len(receipt) + 1,
                "raw_output_tokens": sum(len(parts[name]["output_ids"]) for name in ("public", *receipt)),
                "hybrid_record": hybrid, "hybrid_words": len(hybrid.split()),
                "hybrid_points": 56 + 7 * len(roles), "complete_national_accounts": roles,
                "model_clauses_used_verbatim": [parts[name]["output"] for name in roles],
                "dropped_national_components": sorted(set(receipt) - set(roles)),
            }
    matrix = np.array([
        [ratings[frozenset({left, right} - {None})]["hybrid_points"] for right in slots]
        for left in slots
    ])
    summaries, ceilings = {}, {}
    for prior, arms in routes["arms"].items():
        summaries[prior] = {}
        prior_vector = np.array([row["probability"] for row in arms["silent"]["worlds"]])
        ceilings[prior] = {key: value[0] for key, value in exact(prior_vector, matrix, 0).items()}
        for name, arm in arms.items():
            outcomes = [(row["probability"], ratings[frozenset(slots[a] for a in row["actions"] if a)])
                        for row in arm["worlds"]]
            summaries[prior][name] = {
                "net_routing_reward": arm["net"],
                "mean_raw_points": sum(p * r["raw_points"] for p, r in outcomes),
                "mean_hybrid_points": sum(p * r["hybrid_points"] for p, r in outcomes),
                "mean_model_components": sum(p * r["performed_components"] for p, r in outcomes),
                "both_cards_probability": sum(p for p, r in outcomes if len(r["received"]) == 2),
                "both_accounts_probability": sum(p for p, r in outcomes if len(r["complete_national_accounts"]) == 2),
                "account_probability": {card: sum(p for p, r in outcomes if card in r["complete_national_accounts"])
                                        for card in labels},
                "reference_points_if_both_model_accounts_were_accepted": arm["authored_reference_points"],
            }
    return {"scope": annotations["scope"], "case_sha256": sha256(CASE.read_bytes()).hexdigest(),
            "annotations_sha256": sha256(annotations_path.read_bytes()).hexdigest(),
            "transcript_sha256": sha256((directory / "transcript.jsonl").read_bytes()).hexdigest(),
            "component_scores": parts_scores, "four_records": list(ratings.values()), "arms": summaries,
            "diagnostic_hybrid_ceiling_if_optimized_for_composition": ceilings}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--score", action="store_true")
    args = parser.parse_args()
    value = review(args.directory) if args.score else load(args.directory)[2]
    print(json.dumps(value, indent=2, ensure_ascii=False))
