"""Verify reviewed fresh chair outputs and replay their scores over receipt masks."""
import argparse
from collections import Counter, defaultdict
import csv
from hashlib import sha256
import json
from pathlib import Path
import re

import facilitator_fresh_briefs as study

CITATION = re.compile(r"\[([A-Za-z0-9-]+)\]")


def blind(raw):
    ordered = sorted(raw, key=lambda key: sha256(("review/" + key).encode()).hexdigest())
    return {f"{i:02}": key for i, key in enumerate(ordered, 1)}


def review_inputs(raw):
    inputs = []
    for review_id, key in blind(raw).items():
        row = raw[key]
        payload = json.loads(row["messages"][1]["content"])
        payload.pop("checked_disposition", None)
        inputs.append({"id": review_id, **payload, "response": row["output"], "finished": row["ended"]})
    return inputs


def checks(raw, annotations):
    marks = {row["id"]: row for row in annotations}
    assert marks.keys() == blind(raw).keys() and len(marks) == len(annotations)
    panels = {row[0]: row for row in study.fixtures()}
    grades = {}
    for anon, key in blind(raw).items():
        panel, _ = key.rsplit("/", 1)
        _, _, sources, truth, seen, _, _ = panels[panel]
        mark = marks[anon]
        response = raw[key]["output"]
        heading, delim, brief = response.partition("|")
        brief = brief.strip()
        disposition = heading.strip().casefold() if delim else None
        expected = study.base.decision(truth, seen)
        format_ok = ("\n" not in response and raw[key]["ended"] and bool(brief) and len(brief.split()) <= 48
                     and disposition in ("retain", "revise", "withhold") and "|" not in brief)
        spans = (mark["s1"], mark["s2"])
        assert all(span in response for span in (*spans, mark["issue"]))
        assert bool(mark["issue"]) == bool(mark["reason"])
        cited = set(CITATION.findall(brief))
        citation_ok = cited <= sources.keys() and all(
            bool(span) and f"[S{i+1}]" in span for i, span in enumerate(spans) if i in seen and truth[i] != "unknown"
        )
        criteria = {"disposition": 14 * (disposition == expected), "side_1": 12 * bool(spans[0]),
                    "side_2": 12 * bool(spans[1]), "citations": 10 * citation_ok,
                    "fidelity": 12 * (not mark["issue"]), "format": 10 * format_ok}
        total = sum(criteria.values())
        grades[key] = {"review_id": anon, "points": total, "criteria": criteria,
                       "strict": total == 70, "expected": expected, "disposition": disposition,
                       "false_action": disposition in ("retain", "revise") and disposition != expected,
                       "review": {k: v for k, v in mark.items() if k != "id"}}
    return grades


def replay(grades):
    base = study.base
    data = defaultdict(dict)
    for panel, _, _, truth, seen, actions, reads in study.fixtures():
        case, _ = panel.rsplit("/", 1)
        data[case][seen] = (panel, actions, reads, truth)
    policy = study.transfer.policy(study.transfer.FROZEN)
    modes = (
        ("full_access_pooled", None, None, "pooled"),
        ("same_receipts_pooled", "learned", "agreement", "pooled"),
        ("quote_learned", "learned", "quote", "quote"),
        ("agreement_learned", "learned", "agreement", "agreement"),
        ("agreement_erased", "learned_erased", "agreement", "agreement"),
        ("agreement_greedy", "greedy", "agreement", "agreement"),
    )
    result = {}
    for inventory in ("overlap", "split"):
        result[inventory] = {}
        for name, strategy, reading, writer in modes:
            per_case = {}
            for case, packets in data.items():
                _, _, reads, truth = packets[base.TARGETS]
                if strategy is None:
                    route, masks = {"cost": 0}, {base.TARGETS: 1}
                else:
                    route, masks = base.distribution(strategy, policy, base.base.roster(inventory), truth, reads[reading])
                value = Counter(send_cost=route["cost"])
                for mask, weight in masks.items():
                    panel, actions, _, _ = packets[mask]
                    row = grades[study.request_id(panel, actions[writer])]
                    value["points"] += weight * row["points"]
                    value["false_action"] += weight * row["false_action"]
                    value["strict"] += weight * row["strict"]
                    value["usable_retain"] += weight * (row["strict"] and row["expected"] == "retain")
                    value["usable_revise"] += weight * (row["strict"] and row["expected"] == "revise")
                    value["usable_withhold"] += weight * (row["strict"] and row["expected"] == "withhold")
                per_case[case] = value
            totals = sum(per_case.values(), Counter())
            result[inventory][name] = {"mean": {k: totals[k]/len(data) for k in next(iter(per_case.values()))},
                                       "cases": per_case}
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("review", "score"))
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    raw = study.rows(args.directory)
    if args.mode == "review":
        result = review_inputs(raw)
    else:
        with (args.directory / "review.tsv").open(newline="") as stream:
            annotations = list(csv.DictReader(stream, delimiter="\t"))
        grades = checks(raw, annotations)
        result = {"scope": "Same-assistant exact-span review of newly generated final briefs. Arm labels are "
                           "excluded from the review input. Routing is replayed, with an identical writer per packet.",
                  "grades": grades, "replay": replay(grades),
                  "review_sha256": study.runner.digest(args.directory / "review.tsv")}
    print(json.dumps(result, ensure_ascii=False, indent=2))
