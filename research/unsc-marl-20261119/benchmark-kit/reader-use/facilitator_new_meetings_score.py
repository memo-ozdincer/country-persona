"""Score literal witnesses, exact-span brief reviews, and frozen policy replays."""
import argparse
from collections import Counter
import csv
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_fresh_brief_score as rubric
import facilitator_new_meetings as study
import facilitator_receipt_ceiling as ceiling
from facilitator_scope_rules import CONFLICT, inspect

MODES = ("literal", "override", "verified_only")
policy = ceiling.prior.record
base = policy.base


def read_relations(rows):
    results = {}
    for key, _, claim, source, expected in study.source_rows():
        row = rows[f"{key}/read"]
        parsed = study.witness.read_witness(row["output"], source)
        proposed, admitted, span = parsed if row["ended"] else (None, "unknown", None)
        scoped = inspect(claim, span, source) if admitted == "contradicts" else None
        compatible = scoped is not None and scoped["decision"] != CONFLICT
        unverified = admitted == "contradicts" and scoped is None
        results[key] = {"expected": expected, "proposed": proposed, "span": span, "scope_rule": scoped,
                        "literal": admitted, "override": "unknown" if compatible else admitted,
                        "verified_only": "unknown" if compatible or unverified else admitted}
    return results


def packets():
    for panel, proposal, _, truth, cards in study.panels():
        for mask, flags in enumerate(product((False, True), repeat=2)):
            seen = frozenset(i for i, present in enumerate(flags) if present)
            sources = {f"S{i+1}": cards[i][1] for i in sorted(seen)}
            yield f"{panel}/{mask}", proposal, sources, truth, seen, cards


def annotate(directory, rows):
    with (directory / "review.tsv").open(newline="") as f:
        annotations = list(csv.DictReader(f, delimiter="\t"))
    notes = {row["id"]: row for row in annotations}
    assert notes.keys() == {k for k in rows if not k.endswith("/read")} and len(notes) == len(annotations)
    for key, mark in notes.items():
        assert all(mark[k] in rows[key]["output"] for k in ("s1", "s2", "issue"))
        assert bool(mark["issue"]) == bool(mark["reason"])
    return notes


def grade(rows, notes, reads):
    generated = {k: r for k, r in rows.items() if k.endswith(("/pooled", "/independent"))}
    reviews = {k: notes[k] for k in generated}
    for packet, _, _, _, seen, cards in packets():
        panel, _ = packet.rsplit("/", 1)
        parts, evidence, issues = [], [], []
        finished = True
        for i, (speaker, _) in enumerate(cards):
            if i not in seen:
                line = f"The available evidence does not establish the position of {speaker}."
                parts.append(line)
                evidence.append(line)
                continue
            sid = f"S{i+1}"
            key = f"{panel}/{sid}/field"
            row, mark = rows[key], notes[key]
            text = row["output"]
            parts.append(f"{text} [{sid}]")
            evidence.append(f"{mark['s1']} [{sid}]" if mark["s1"] == text else "")
            assert (not mark["s1"] or mark["s1"] == text) and not mark["s2"]
            finished &= row["ended"] and len(text.split()) <= 21 and bool(text) and "\n" not in text
            if mark["issue"]:
                issues.append((mark["issue"], mark["reason"]))
        for mode in MODES:
            readings = tuple(reads[f"{panel}/S{i}"][mode] for i in (1, 2))
            disposition = base.decision(readings, seen)
            key = f"{packet}/{mode}"
            generated[key] = {"output": f"{disposition} | {' '.join(parts)}", "ended": finished}
            issue, reason = issues[0] if issues else ("", "")
            reviews[key] = {"s1": evidence[0], "s2": evidence[1], "issue": issue, "reason": reason}
    notes_by_alias = [{**reviews[key], "id": alias} for alias, key in rubric.blind(generated).items()]
    def rubric_packets():
        for packet, proposal, sources, truth, seen, _ in packets():
            yield packet, proposal, sources, truth, seen, {}, {}

    with patch.object(rubric.study, "fixtures", rubric_packets):
        scores = rubric.checks(generated, notes_by_alias)
    return {key: {"response": row["output"], **scores[key]} for key, row in generated.items()}


def bank(reads, scored):
    receipts = []
    for packet, _, _, _, seen, _ in packets():
        panel, _ = packet.rsplit("/", 1)
        for mode in MODES:
            vector = tuple(reads[f"{panel}/S{i}"][mode] for i in (1, 2))
            result = scored[f"{packet}/{mode}"]
            receipts.append((panel, mode, seen, vector, result["expected"], result["disposition"], result["strict"]))
    return policy.collect(receipts)


def routing(cases):
    fitted, independent = ceiling.stock()
    baselines = (("frozen", "learned", fitted), ("erased", "learned_erased", fitted),
                 ("trained_independent", "learned_erased", independent), ("greedy", "greedy", {}))
    results = {}
    with patch.object(policy, "MODES", MODES):
        for inventory in ("split", "overlap"):
            compared = policy.evaluate(cases, baselines, inventory)
            frozen, upper_bounds = compared["frozen"]["summary"], {}
            for mode in MODES:
                cohort = {k: row for k, row in cases.items() if k[1] == mode}
                _, adaptive = ceiling.solve(cohort, inventory, True)
                _, no_ack = ceiling.solve(cohort, inventory, False)
                assert adaptive["exact_net"] + 1e-9 >= max(no_ack["exact_net"], frozen[mode]["brief_net"])
                upper_bounds[mode] = {"adaptive": adaptive, "independent": no_ack}
            results[inventory] = {"policies": compared, "upper_bounds": upper_bounds}
    return results


def score(directory):
    rows = study.verify(directory)
    reviews = annotate(directory, rows)
    reads = read_relations(rows)
    scored = grade(rows, reviews, reads)
    summary = {}
    for mode in ("pooled", "independent", *MODES):
        selection = [row for key, row in scored.items() if key.endswith(f"/3/{mode}")]
        totals = Counter()
        for row in selection:
            totals.update({"records": 1, "correct_action": row["disposition"] == row["expected"],
                           "strict": row["strict"], "points": row["points"], "false_action": row["false_action"]})
        summary[mode] = totals
    costs = {mode: Counter() for mode in ("read", "field", "pooled", "independent")}
    for key, row in rows.items():
        costs[key.rsplit("/", 1)[1]].update(
            {"calls": 1, "input": len(row["input_ids"]), "output": len(row["output_ids"])})
    paths = (Path(__file__), Path(rubric.__file__), Path(ceiling.__file__), Path(policy.__file__),
             Path(inspect.__code__.co_filename), ceiling.POLICIES, study.chair.transfer.FROZEN,
             directory / "transcript.jsonl", directory / "review.tsv")
    return {"scope": "Two previously unused meeting families, one frozen language model, exact receipt replay, zero updates. "
                     "Solo and independent full-packet runs have unequal compute to routed records. Source cards are "
                     "curator paraphrases. Semantic reviews are same-assistant annotations.",
            "verified_generations": len(rows), "token_costs": costs, "source_relations": reads,
            "scope_coverage": sum(row["scope_rule"] is not None for row in reads.values()),
            "full_packet": summary, "grades": scored, "routing": routing(bank(reads, scored)),
            "input_sha256": {path.name: study.runner.digest(path) for path in paths}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    print(json.dumps(score(parser.parse_args().directory), indent=2, ensure_ascii=False))
