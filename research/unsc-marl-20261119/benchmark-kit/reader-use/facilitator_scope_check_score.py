"""Score the compatibility gate and replay its transmitted relations."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_scope_check as study

ceiling = study.ceiling
base = ceiling.base
WRITER = study.HERE / "facilitator-witness-writer-evidence/results.json"
MODES = ("original", "checked", "suppress_all", "authored_check")


def decisions(rows):
    audit = {}
    for key, payload, reference in study.cases():
        captured = rows[key]
        line = captured["output"]
        proposed = study.parse(captured)
        within_budget = len(line.partition("|")[2].split()) <= 25
        admitted = proposed if within_budget else None
        audit[key] = {"expected": reference, "admitted": admitted, "valid": admitted is not None,
                      "correct": admitted == reference, "output": line, "inputs": payload,
                      "input_tokens": len(captured["input_ids"]), "output_tokens": len(captured["output_ids"])}
    return audit


def receipt_bank(cohorts, audits, writer):
    evaluated = {}
    for family, data in cohorts.items():
        records = []
        for (panel, _), real in data.items():
            labels = real["reads"]
            observed = {
                "original": labels,
                "checked": tuple(("unknown" if r == "contradicts" and audits[f"{panel}/S{i+1}"]["admitted"] != "conflict" else r)
                                 for i, r in enumerate(labels)),
                "suppress_all": tuple("unknown" if r == "contradicts" else r for r in labels),
                "authored_check": tuple(("unknown" if r == "contradicts" and audits[f"{panel}/S{i+1}"]["expected"] != "conflict" else r)
                                        for i, r in enumerate(labels)),
            }
            for arm, readings in observed.items():
                for mask, old in real["receipts"].items():
                    # Other briefs stay unchanged. Suppressing a contradiction
                    # can only turn a revision into a withhold.
                    predicted = base.decision(readings, mask)
                    correct = old["expected"] == predicted
                    if predicted == old["action"]:
                        strict = old["strict"]
                    elif correct:
                        assert predicted == "withhold"
                        slot = 2 * int(0 in mask) + int(1 in mask)
                        archived = writer[f"{panel}/{slot}/withhold"]["grade"]
                        assert archived["expected"] == predicted == archived["disposition"]
                        strict = archived["strict"]
                    else:
                        strict = False
                    records.append((panel, arm, mask, readings, old["expected"], predicted, strict))
        evaluated[family] = ceiling.prior.record.collect(records)
    return evaluated


def replay(bank):
    frozen, independent = ceiling.stock()
    systems = (("frozen", "learned", frozen), ("frozen_erased", "learned_erased", frozen),
               ("trained_independent", "learned_erased", independent), ("greedy", "greedy", {}))
    result = {}
    with patch.object(ceiling.prior.record, "MODES", MODES):
        for family, cases in bank.items():
            result[family] = {roster: ceiling.prior.record.evaluate(cases, systems, roster)
                              for roster in ("split", "overlap")}
    return result


def summary(audit):
    totals = {}
    for key, row in audit.items():
        split = "controls" if key.startswith("control/") else "routed"
        count = totals.setdefault(split, Counter())
        count["cases"] += 1
        count["correct"] += row["correct"]
        count["sound_explanation"] += row["explanation_review"]["sound"] == "yes"
        count["invalid"] += not row["valid"]
        count["false_conflict"] += row["admitted"] == "conflict" and row["expected"] != "conflict"
        count["missed_conflict"] += row["admitted"] != "conflict" and row["expected"] == "conflict"
        count["input_tokens"] += row["input_tokens"]
        count["output_tokens"] += row["output_tokens"]
    return totals


def score(directory):
    audited = decisions(study.read(directory))
    with (directory / "explanation-review.tsv").open(newline="") as stream:
        annotations = list(csv.DictReader(stream, delimiter="\t"))
    explanations = {row["id"]: row for row in annotations}
    assert explanations.keys() == audited.keys() and len(explanations) == len(annotations)
    for key, row in audited.items():
        marked = explanations[key]
        assert marked["span"] and marked["span"] in row["output"]
        assert marked["sound"] in ("yes", "no") and (marked["sound"] == "yes" or marked["issue"])
        row["explanation_review"] = marked
    archived = study.base.load(WRITER)["records"]["assertion"]
    bank = receipt_bank(ceiling.datasets(), audited, archived)
    measured = replay(bank)
    for roster in ("split", "overlap"):
        for family in measured:
            reference = study.base.load(ceiling.HERE / "facilitator-receipt-ceiling-results.json")["evidence"][family][roster]
            left = measured[family][roster]["frozen"]["summary"]["original"]
            assert left == reference["results"]["frozen_adaptive"]["summary"][ceiling.MODE]
    return {"scope": "Recheck only a prior contradiction backed by a literal quote. An admitted conflict preserves "
                     "the unchanged label and all other outputs defer. Proof explanations are recorded; their content "
                     "does not serve as a deterministic gate. Official case and prose keys are used only in scoring "
                     "and the separately labelled authored upper comparison.",
            "audit": audited, "scope_summary": summary(audited), "policy_replay": measured,
            "input_sha256": {p.name: study.runner.digest(p) for p in
                             (WRITER, directory / "transcript.jsonl", directory / "explanation-review.tsv")}}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    print(json.dumps(score(p.parse_args().directory), indent=2, ensure_ascii=False))
