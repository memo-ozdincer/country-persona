"""Score original-claim decisions separately from the generated body."""
import argparse
from collections import Counter
import json
from pathlib import Path

import facilitator_attribution_choices as study
import facilitator_verified_brief_score as brief

BOTH = frozenset({0, 1})


def score(directory):
    rows = study.verify(directory)
    marks = brief.table(directory / "review.tsv")
    assert marks.keys() == {k for k in rows if k.endswith("/body")}
    reads = study.readings(rows)
    relation_counts, composition, by_arm = Counter(), {}, {}
    checks = {}
    for name, scenario in study.panels():
        truth = scenario["expected"]
        local = [reads[f"{name}/S{i}"] for i in (1, 2)]
        for i, (target, evidence) in enumerate(zip(truth, local, strict=True), 1):
            obs = evidence["observations"]
            relation_counts.update({"attributions": 1, "strict_stable_correct": evidence["stable"] == target,
                                    "fallback_correct": evidence["fallback"] == target,
                                    "order_unstable": evidence["stable"] is None,
                                    "observations_correct": sum(status == target for status in obs),
                                    "observations_unparsed": sum(status is None for status in obs)})
            checks[f"{name}/S{i}"] = {"expected": target, **evidence}

        expected_heading = study.transfer.chair.base.decision(truth, BOTH)
        heading = study.transfer.chair.base.decision(tuple(r["fallback"] for r in local), BOTH)
        council = f"{scenario['council']} [S0]"
        common_message = None
        for arm in study.ARMS:
            key = f"{name}/{arm}/body"
            row = rows[key]
            body = row["output"]
            payload = json.loads(row["messages"][1]["content"])
            supplied = payload.pop("findings", None)
            if arm == "body_alone":
                assert supplied is None
                common_message = payload
            else:
                assert payload == common_message
                assert supplied == {f"S{i}": item["fallback"] for i, item in enumerate(local, 1)}
            author = marks[key]
            assert all(author[k] in body for k in ("s1", "s2", "issue"))
            valid_body = row["ended"] and "\n" not in body and "|" not in body and 0 < len(body.split()) <= 40
            combined = {"output": f"{heading} | {council} {body}", "ended": valid_body}
            review = {"council": council, **{k: author[k] for k in ("s1", "s2", "issue", "reason")}}
            grade = brief.grade(combined, review, truth)
            assert grade["expected"] == expected_heading
            output = {"body_compliant": valid_body, "heading_from_compared_claims": heading, **grade}
            composition[key] = output
            counts = by_arm.setdefault(arm, Counter())
            counts.update({"records": 1, "points": grade["points"], "strict": grade["strict"],
                           "disposition_correct": expected_heading == heading,
                           "body_format_ok": valid_body, "fidelity_error": bool(author["issue"]),
                           "body_input_tokens": len(row["input_ids"]), "body_output_tokens": len(row["output_ids"])})
    files = (Path(__file__), Path(brief.__file__), directory / "review.tsv", directory / "transcript.jsonl")
    return {"scope": "Three candidate rotations per attribution, with same-assistant body review. "
                     "Both body arms share the assembled Council block and decision. The only input treatment "
                     "is the findings field. Cards and opposed prompts are previously exposed or adapted from exposed cases.",
            "verified_generations": len(rows), "relations": relation_counts, "record_arms": by_arm,
            "reading_audit": checks, "records": composition,
            "sha256": {p.name: study.runner.digest(p) for p in files}}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    print(json.dumps(score(p.parse_args().directory), indent=2, ensure_ascii=False))
