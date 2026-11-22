"""Prepare arm-hidden final review and score exact evidence spans and delivery."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re

import facilitator_requested_evidence as test

POINTS = {"decision": 14, "abstention": 14, "editorial": 21, "limit": 14, "citations": 7}
CITATION = re.compile(r"\[(S\d+|[A-Z])\]")


def review_items(rows):
    items = {}
    for name, request, public, cards in test.cases():
        for arm in test.ARMS:
            address = f"{name}/{arm}/final"
            visible = public | {k: cards[k] for k in test.receipt(name, arm, rows)}
            text = rows[address]["output"]
            key = sha256(json.dumps([name, visible, text], sort_keys=True).encode()).hexdigest()[:16]
            item = {"task": request, "criterion": test.packet()["tasks"][name]["criterion"],
                    "evidence_delivered": visible, "output": text}
            items.setdefault(key, {"item": item, "addresses": []})["addresses"].append(address)
            assert items[key]["item"] == item
    return dict(sorted(items.items()))


def grade(review, output, visible, target):
    assert set(review) == {*POINTS, "integrity"}
    for criterion, mark in review.items():
        assert len(mark) == 2
        status, span = mark
        assert status in ("met", "unmet", "uncertain") and (not span or span in output)
        if status == "met":
            assert span
            if criterion == "editorial":
                assert target in visible
            elif criterion == "citations":
                cited = set(CITATION.findall(output))
                assert {"S0", "S1"} <= cited <= visible.keys()
                if review["editorial"][0] == "met":
                    assert target in cited
    points = sum(weight for k, weight in POINTS.items() if review[k][0] == "met")
    return {"points": points, "strict_fields": points == 70 and review["integrity"][0] == "met"}


def call_ids(rows, name, arm, deck):
    calls = [f"{name}/{arm}/final"]
    if arm in ("peer", "independent", "solo"):
        calls.append(f"{name}/opening")
    if arm == "independent":
        calls.append(f"{deck}/independent/selection")
    elif arm in ("peer", "verbatim_query", "solo"):
        calls.append(f"{name}/{arm}/selection")
    assert all(key in rows for key in calls)
    return calls


def score(rows, items, grades):
    assert grades.keys() == items.keys()
    report = {}
    for key, record in items.items():
        output = record["item"]["output"]
        visible = record["item"]["evidence_delivered"]
        for address in record["addresses"]:
            name, arm, _ = address.split("/")
            case = test.packet()["tasks"][name]
            target = case["target"]
            points = grade(grades[key], output, visible, target)
            evidence = test.receipt(name, arm, rows)
            attempted = call_ids(rows, name, arm, case["deck"])
            strict = points.pop("strict_fields") and rows[address]["ended"] and len(output.split()) <= 95
            report[f"{name}/{arm}"] = {**points, "strict": strict, "review_item": key, "evidence": evidence,
                                      "target_visible": target in evidence,
                                      "editorial_met": grades[key]["editorial"][0] == "met",
                                      "integrity_met": grades[key]["integrity"][0] == "met",
                                      "calls": len(attempted), "peer_question_turns": int(arm == "peer"),
                                      "input_tokens": sum(len(rows[k]["input_ids"]) for k in attempted),
                                      "output_tokens": sum(len(rows[k]["output_ids"]) for k in attempted)}
    summary = {}
    for arm in test.ARMS:
        cohort = [v for k, v in report.items() if k.endswith(f"/{arm}")]
        summary[arm] = {k: sum(v[k] for v in cohort) for k in (
            "strict", "target_visible", "editorial_met", "integrity_met", "peer_question_turns",
            "calls", "input_tokens", "output_tokens")}
        summary[arm]["mean_points"] = sum(v["points"] for v in cohort) / len(cohort)
    attribution = {}
    for name, _, _, _ in test.cases():
        arms = {arm: report[f"{name}/{arm}"] for arm in test.ARMS}
        attribution[name] = {
            "question": rows[f"{name}/opening"]["output"],
            "peer_received": arms["peer"]["evidence"],
            "peer_editorial_gain_over_independent": arms["peer"]["editorial_met"] and not arms["independent"]["editorial_met"],
            "peer_editorial_gain_over_verbatim": arms["peer"]["editorial_met"] and not arms["verbatim_query"]["editorial_met"],
        }
    return {"source": "Same-assistant annotation using arm-hidden final cards. Identical view and text judged once.",
            "unique_review_items": len(items), "summary": summary, "peer_attribution": attribution, "records": report}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("run", type=Path)
    p.add_argument("--grades", type=Path)
    args = p.parse_args()
    rows = test.verify(args.run)
    items = review_items(rows)
    result = (score(rows, items, json.loads(args.grades.read_text())) if args.grades
              else {k: v["item"] for k, v in items.items()})
    print(json.dumps(result, indent=2, ensure_ascii=False))
