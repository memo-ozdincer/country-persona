"""Compare the generated writer arms at matched receipt masks and frozen routing weights."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_bound_field_score as bound
import facilitator_event_transfer_score as transfer
import facilitator_fresh_brief_score as grade
import facilitator_witness_writer as run

DEV_GRADES = run.HERE / "facilitator-bound-field-evidence/results.json"


def review_packet(rows):
    result = []
    for alias, key in grade.blind(rows).items():
        row = rows[key]
        payload = json.loads(row["messages"][1]["content"])
        payload.pop("exact_excerpt", None)
        result.append({"id": alias, **payload, "response": row["output"], "finished": row["ended"]})
    return result


def measure(directory, rows):
    blinded = {alias: rows[key] for alias, key in grade.blind(rows).items()}
    checked = bound.semantic_review(directory, blinded)
    marks = {key: checked[alias] for alias, key in grade.blind(rows).items()}

    base = run.base
    dev_archive = base.load(DEV_GRADES)
    old_transfer = base.load(run.TRANSFER)
    test_packets = {k: v["sources"] for k, v in base.load(run.held.PACK).items()}
    transfer_cases = []
    for packet, claim, truth, seen, receipts, _ in run.held.packets():
        panel = packet.rsplit("/", 1)[0]
        relations = {mode: tuple(old_transfer["readings"][f"{panel}/S{i}"][mode] for i in (1, 2))
                     for mode in ("quote", "agreement")}
        relations["oracle"] = truth
        actions = {mode: base.base.decision(values, seen) for mode, values in relations.items()}
        transfer_cases.append((packet, claim, receipts, truth, seen, actions, relations))
    params = base.transfer.policy(base.transfer.FROZEN)
    fresh = base.load(grade.study.HERE / "facilitator-fresh-brief-evidence/results.json")
    old_pooled = {k: v for k, v in fresh["grades"].items() if k.endswith("/pooled")}
    outputs = {"development": {"original": dev_archive["replay"]},
               "transfer": {"original": old_transfer["replay"]}}
    records = {}
    fields = list(run.fixtures())
    for arm in run.ARMS:
        selected = {key: f"{key}/{arm}" if span and arm == "witness" else f"{key}/assertion" for key, _, span in fields}
        values = {key: rows[record] for key, record in selected.items()}
        scores = {key: marks[record] for key, record in selected.items()}
        dev_records, dev_grades = bound.render(values, scores)
        assert dev_grades.keys() == dev_archive["grades"].keys()
        outputs["development"][arm] = grade.replay(old_pooled | dev_grades)
        with patch.object(base, "fixtures", side_effect=lambda: iter(transfer_cases)), \
             patch.object(base.transfer, "packets", return_value=test_packets):
            test_records, test_grades = bound.render(values, scores)
        assert test_grades.keys() == old_transfer["bound_grades"].keys()
        outputs["transfer"][arm] = transfer.replay(transfer_cases, params, old_transfer["syntheses"], test_grades)
        records[arm] = {key: {"grade": data, "record": (dev_records | test_records)[key]["output"]}
                        for key, data in sorted((dev_grades | test_grades).items())}
    field_summary = {}
    for docket in ("development", "transfer"):
        case_keys = [k for k, _, _ in fields if (k.startswith(("abyei-", "central-african-republic-"))) == (docket == "transfer")]
        archive = dev_archive if docket == "development" else old_transfer
        systems = {"original": archive["fields"]}
        for arm in run.ARMS:
            systems[arm] = {key: marks.get(f"{key}/{arm}", marks[f"{key}/assertion"]) for key in case_keys}
        field_summary[docket] = {name: {"cases": len(case_keys),
                                       "complete": sum(bool(arm[k]["supported_span"]) for k in case_keys),
                                       "error_free_complete": sum(bool(arm[k]["supported_span"]) and not arm[k]["issue_span"] for k in case_keys),
                                       "critical_error": sum(bool(arm[k]["issue_span"]) for k in case_keys)}
                                 for name, arm in systems.items()}
    return {"scope": "Paired same-model assertion-only and exact-witness field drafting with arm-hidden same-assistant review. "
                     "No witness fallback uses the assertion-only generation. Policies and receipt labels are frozen.",
            "field_summary": field_summary, "field_review": marks, "records": records, "replay": outputs,
            "inputs_sha256": {str(p.relative_to(run.HERE) if p.is_relative_to(run.HERE) else p.name):
                              run.runner.digest(p) for p in (DEV_GRADES, run.TRANSFER, directory / "review.tsv",
                                                            directory / "transcript.jsonl")}}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("review", "score"))
    p.add_argument("directory", type=Path)
    args = p.parse_args()
    captured = run.read(args.directory)
    answer = review_packet(captured) if args.mode == "review" else measure(args.directory, captured)
    print(json.dumps(answer, ensure_ascii=False, indent=2))
