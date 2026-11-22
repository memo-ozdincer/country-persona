"""Verify source-ID claims, then replay the same routes on admitted evidence."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import facilitator_cited_2699 as study

archive = study.archive
source = study.SOURCE


def assess(rows):
    checks = {}
    for key, view, registry, expected in study.cases():
        row = rows[key]
        found = row["output"].split()
        valid = (row["ended"] and len(found) == 3 and row["output"] == " ".join(found)
                 and all(token in registry or token == "X" for token in found))
        selected = found if valid else [None] * 3
        witnesses = view["source_sentences"]
        fields = []
        for target, given, claim in zip(expected, selected, view["claims"], strict=True):
            fields.append({"claim": claim, "expected": target, "given": given,
                           "exact_source": witnesses.get(given), "correct": given == target,
                           "unexpected_evidence": target == "X" and given in registry})
        checks[key] = {"valid": valid, "full_match": valid and all(f["correct"] for f in fields), "fields": fields,
                       "input_tokens": len(row["input_ids"]), "output_tokens": len(row["output_ids"])}
    assert checks.keys() == rows.keys()
    return checks


def summarize(checks):
    report = {}
    for group in ("full", "withheld", "foil"):
        group_rows = [row for key, row in checks.items() if f"/{group}/" in key]
        fields = [f for row in group_rows for f in row["fields"]]
        report[group] = {"calls": len(group_rows), "valid_outputs": sum(r["valid"] for r in group_rows),
                         "complete_matches": sum(r["full_match"] for r in group_rows),
                         "correct_fields": sum(f["correct"] for f in fields), "fields": len(fields),
                         "absent_fields": sum(f["expected"] == "X" for f in fields),
                         "false_citations": sum(f["unexpected_evidence"] for f in fields)}
    return report


def replay(checks):
    old = json.loads((archive.EVIDENCE / "results.json").read_text())
    table = np.zeros((len(study.ORDERS), 4), dtype=bool)
    for name, deck in study.decks().items():
        for order in range(len(study.ORDERS)):
            table[order, deck["topic"]] = checks[f"{name}/full/{order}"]["full_match"]
    modes = {"first_read": table[0], "second_read": table[1], "double_read": table.all(axis=0)}
    results = {}
    with patch.object(source, "packet", archive.packet):
        for label in source.PRIORS:
            prior = source.ROUTE.TEST_PRIORS[label]
            policies = source.policies(prior)
            output = {}
            for arm, policy in policies.items():
                prior_scores = old["priors"][label]["all_arms"][arm]
                output[arm] = {mode: source.distribution(policy, prior, old["decoded"], np.broadcast_to(mask, (4, 4)))
                               for mode, mask in modes.items()}
                output[arm].update({mode: prior_scores[mode] for mode in ("visible", "source_only", "typed")})
                for mode in modes:
                    assert abs(output[arm][mode]["cost"] - prior_scores["source_only"]["cost"]) < 1e-12
            results[label] = output
    return {"admitted_topics": {mode: np.flatnonzero(mask).tolist() for mode, mask in modes.items()},
            "priors": results}


def evaluate(rows):
    checks = assess(rows)
    return {"calls": len(rows), "input_tokens": sum(r["input_tokens"] for r in checks.values()),
            "output_tokens": sum(r["output_tokens"] for r in checks.values()),
            "diagnostic": summarize(checks), "checks": checks, "routing_replay": replay(checks)}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    print(json.dumps(evaluate(study.verify(args.directory)), ensure_ascii=False, indent=2))
