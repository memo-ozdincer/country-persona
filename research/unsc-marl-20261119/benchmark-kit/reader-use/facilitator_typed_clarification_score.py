"""Assemble chair headings from learned source judgments and check the released text."""
import argparse
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_typed_clarification as study
import facilitator_clarification_score as legacy
import facilitator_deliberation_score as rubric
import facilitator_fresh_brief_score as grade
import facilitator_record_policy as replay
from facilitator_policy_audit import freeze

BASELINE = study.HERE / "facilitator-clarification-evidence/results.json"
NOTES = study.HERE / "facilitator-deliberation-evidence/transcript.jsonl"
FEEDBACK = study.HERE / "facilitator-feedback-cost-results.json"
UNCERTAINTY = "This side of the joint claim remains unverified."
MODES = ("direct", "asked", "authored")


def notes():
    return {row["id"]: row for row in map(json.loads, NOTES.read_text().splitlines())
            if "/independent/revision" in row["id"]}


def compose(action, phrases, relations, speakers, seen):
    fields = []
    for i, (phrase, relation) in enumerate(zip(phrases, relations, strict=True), 1):
        if i - 1 not in seen:
            fields.append(f"The available evidence does not establish the position of {speakers[i-1]}.")
            continue
        field = f"{phrase} [S{i}]"
        if relation == "unknown":
            field += f" {UNCERTAINTY}"
        fields.append(field)
    return f"{action} | {' '.join(fields)}", fields


def review_bound(panel, spans, relations, seen):
    # The two source-local sentences in each panel were already reviewed.
    # The China draft-circulation note covers the related consultation only.
    if panel == "afghanistan-1" and 0 in seen and relations[0] != "unknown":
        return ("", spans[1])
    return tuple(spans)


def route(cases, modes=("direct", "asked")):
    old = replay.dev.load(FEEDBACK)["independent_policy"]
    independent = {freeze(row["state"]): row["probabilities"] for row in old}
    frozen = replay.dev.transfer.policy(replay.dev.transfer.FROZEN)
    systems = (("frozen", "learned", frozen), ("frozen_erased", "learned_erased", frozen),
               ("independent", "learned_erased", independent), ("greedy", "greedy", {}))
    with patch.object(replay, "MODES", modes):
        return {inventory: replay.evaluate(replay.collect(cases), systems, inventory)
                for inventory in ("split", "overlap")}


def run(directory, capture="actions.jsonl"):
    raw, readings = study.read(directory)
    archive = study.prior.base.load(BASELINE)
    replies = study.prior.base.load(study.SOURCE)[study.prior.FAMILY]
    fields = notes()
    actual, annotations, fixtures = {}, {}, []
    traces = {}
    receipt_keys = {}
    for panel, proposal, _, expected, _, cards, _, target, _ in study.prior.source_inputs():
        truth = rubric.RELATIONS[expected]
        sources = {f"S{i+1}": c[1] for i, c in enumerate(cards)}
        records = [fields[f"{panel}/independent/revision{i+1}"] for i in range(2)]
        phrases = [row["output"] for row in records]
        finished = all(row["ended"] and len(row["output"].split()) <= 21 and "\n" not in row["output"]
                       for row in records)
        for mode in MODES:
            observed = tuple(readings[f"{panel}/S{i+1}/{'asked' if mode == 'asked' and target == i else 'direct'}"]["admitted"]
                             for i in range(2)) if mode != "authored" else truth
            action = grade.study.base.decision(observed, frozenset({0, 1}))
            traces[f"{panel}/{mode}"] = {"relations": observed, "reference": truth, "decision": action}
            for mask, flags in enumerate(product((False, True), repeat=2)):
                seen = frozenset(i for i, present in enumerate(flags) if present)
                prefix = f"{panel}/{mode}" if mask == 3 else f"{panel}/{mode}/mask{mask}"
                key = f"{prefix}/bound"
                decision = grade.study.base.decision(observed, seen)
                record, parts = compose(decision, phrases, observed, [card[0] for card in cards], seen)
                side1, side2 = review_bound(panel, parts, observed, seen)
                actual[key] = {"output": record, "ended": finished}
                misleading = any(observed[i] == "unknown" and truth[i] != "unknown" for i in seen)
                annotations[key] = {"s1": side1, "s2": side2,
                                    "issue": UNCERTAINTY if misleading else "",
                                    "reason": "The cited source establishes or rules out a side described as unverified."
                                    if misleading else ""}
                visible = {f"S{i+1}": sources[f"S{i+1}"] for i in sorted(seen)}
                fixtures.append((prefix, proposal, visible, truth, seen, {}, {}))
                if mode != "authored":
                    receipt_keys[key] = (panel, mode, seen, observed)
            if mode != "authored":
                old_mode = "asked" if mode == "asked" else "independent"
                archive_key = f"{panel}/{old_mode}/final"
                old = replies[archive_key]
                _, sep, body = old.partition("|")
                assert sep
                key = f"{panel}/{mode}/heading_only"
                mark = archive["episodes"][panel][old_mode]["final"]
                actual[key] = {"output": f"{action} |{body}", "ended": mark["criteria"]["format"] == 10}
                annotations[key] = mark["review"]
    blinded = [{"id": anon, **annotations[key]} for anon, key in grade.blind(actual).items()]
    with patch.object(grade.study, "fixtures", return_value=fixtures):
        reviewed = grade.checks(actual, blinded)
    aggregates = {}
    local_accuracy = {}
    for mode in MODES:
        chosen = [row for key, row in traces.items() if key.endswith(f"/{mode}")]
        correct = sum(actual == reference for row in chosen for actual, reference in
                      zip(row["relations"], row["reference"], strict=True))
        local_accuracy[mode] = {"correct": correct, "total": 2 * len(chosen)}
        aggregates[mode] = {}
        for writer in ("bound", "heading_only"):
            selection = [v for k, v in reviewed.items() if k.endswith(f"/{mode}/{writer}")]
            if selection:
                aggregates[mode][writer] = {"headings_correct": sum(v["criteria"]["disposition"] == 14 for v in selection),
                                            "strict": sum(v["strict"] for v in selection),
                                            "false_action": sum(v["false_action"] for v in selection),
                                            "mean_points": sum(v["points"] for v in selection) / len(selection)}
    return {"scope": "Constrained local relation inference with frozen drafted fields. The runtime composes the "
                     "heading from predictions. The authored arm is a writer ceiling. No gold relation enters "
                     "either model-controlled arm. Only the heading is changed in the heading-only intervention.",
            "classifications": readings, "local_accuracy": local_accuracy, "decisions": traces, "summary": aggregates,
            "simulated_delivery": route([(*context, reviewed[key]["expected"], reviewed[key]["disposition"], reviewed[key]["strict"])
                                         for key, context in receipt_keys.items()]),
            "final_records": {k: actual[k]["output"] for k in sorted(actual)}, "review": reviewed,
            "classifications_calls": len(raw),
            "input_sha256": {p.name: study.prior.runner.digest(p)
                             for p in (BASELINE, NOTES, FEEDBACK, directory / capture)}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    print(json.dumps(run(parser.parse_args().directory), indent=2, ensure_ascii=False))
