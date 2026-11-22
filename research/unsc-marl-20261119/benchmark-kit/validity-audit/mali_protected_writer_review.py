"""Apply locked local annotations, compose Mali receipts and replay matched controls."""
import argparse
import json
from pathlib import Path
import re
from unittest.mock import patch

import numpy as np

import mali_protected_writer as writer
import mali_request_writer_review as review
from source_request_policy import BITS, TEST_PRIORS, evaluate, exact_optional, receipt_matrix


FIELDS = ("french-uae", "russia", "france-after")
PUBLIC_POINTS = 56


def assemble(directory, trusted_citations):
    rows = {row["id"]: row for row in writer.replay(directory)}
    marks = json.loads((directory / "annotations.json").read_text())
    sha = review.digest(directory / "transcript.jsonl")
    assert marks["transcript_sha256"] == sha and marks["parts"].keys() == rows.keys()
    admitted = {}
    for name, row in rows.items():
        mark = marks["parts"][name]
        candidate = row["output"]
        assert mark["candidate"] == candidate and mark["reason"].strip()
        if mark["admit"]:
            assert row["ended"] and 0 < len(candidate.split()) <= 22
            if trusted_citations:
                assert row["evidence_ids"] == [name]
                suffix = re.fullmatch(r"(.*) \[[\w-]+\]", candidate)
                assert suffix is not None and not review.citations(suffix[1])
                candidate = f"{suffix[1]} [{name}]"
            if not candidate.endswith(f"[{name}]") or review.citations(candidate) != {name}:
                continue
            assert mark["source_quote"] and mark["source_quote"] in writer.blocks()[name]
            admitted[name] = candidate

    paragraphs = writer.PUBLIC.split("\n\n")
    outputs, records = [], {}
    for mask in range(8):
        seen = [field for i, field in enumerate(FIELDS) if mask & (1 << i)]
        used = [f for f in seen if f in admitted]
        answer = "\n\n".join([writer.PUBLIC, *(admitted[f] for f in used)])
        key = f"protected-{mask}"
        outputs.append({"id": key, "output": answer, "ended": True,
                        "evidence_ids": ["docket", "status-638", "status-639", *seen],
                        "input_ids": [], "output_ids": []})
        met = {}
        for criterion, sources in writer.PUBLIC_PARTS.items():
            excerpt = paragraphs[0] if sources == ["status-638"] else paragraphs[1] if sources == ["status-639"] else paragraphs[2]
            met[criterion] = [excerpt, sources]
        for criterion, field in review.PRIVATE_RATIONALES.items():
            if field in used:
                end = answer.index(admitted[field]) + len(admitted[field])
                met[criterion] = [answer[:end], ["status-638", "status-639", field]]
        records[key] = {"met": met,
                        "retained_france_objection": admitted["france-after"] if "france-after" in used else "",
                        "guard": {"status": "clear", "response": "", "source": [],
                                  "reason": "Fixed public wording was checked against the official record, and only admitted source-local paragraphs were included."}}

    with patch.object(review, "replay", return_value=outputs):
        receipts = review.score_records(directory, {"transcript_sha256": sha, "records": records})
    for result, row, detail in zip(receipts, outputs, records.values(), strict=True):
        del result["input_tokens"], result["output_tokens"]
        result["national_points"] = result["raw_points"] - PUBLIC_POINTS
        result["record"] = row["output"]
        result["admitted_components"] = [name for name, text in admitted.items() if text in row["output"]]
        result["criterion_evidence"] = detail["met"]
        assert result["eligible"] and not result["citation_not_in_credited_span"]
    return receipts, marks


def run(directory, exact, trusted_citations):
    receipts, marks = assemble(directory, trusted_citations)
    evidence = directory.parent
    policy = evidence / "source-request-policy.json"
    readers = {"joint_reader": evidence / "mali-source-request-reader" / "score.json",
               "scoped_reader": evidence / "mali-request-term" / "score.json"}
    results = review.policies(policy, receipts, readers)
    raw = np.asarray([r["raw_points"] for r in receipts])
    bounds = {}
    transfer = {}
    if exact:
        payoff = receipt_matrix(raw, review.LOSS)
        for name, prior in TEST_PRIORS.items():
            optimal, examined = exact_optional(prior, payoff, review.LOSS)
            upper = evaluate(optimal, prior, raw, review.LOSS)
            upper["request_maps_examined"] = examined
            upper["expected_final_points"] = upper.pop("proof_points")
            upper["policy"] = [part.tolist() for part in optimal]
            fixed = next(r for r in results if r["reader"] == "typed" and r["prior"] == name
                         and r["reward"] == "raw_points")
            assert all(z["net"] <= upper["net"] + 1e-9 for z in fixed["arms"].values())
            bounds[name] = upper
            transfer[name] = {test: evaluate(optimal, target, raw, review.LOSS)["net"]
                              for test, target in TEST_PRIORS.items()}
    learned = json.loads(policy.read_text())["training"]
    ask, send, reply = learned["request"][1], learned["left_delivery"][1], learned["reply"][3]
    return {"scope": marks["scope"], "annotations_sha256": review.digest(directory / "annotations.json"),
            "policy_sha256": review.digest(policy),
            "decoders_sha256": {name: review.digest(path) for name, path in readers.items()},
            "fixed_public_points": PUBLIC_POINTS, "trusted_citations": trusted_citations,
            "loss": review.LOSS, "records": receipts, "comparisons": results,
            "exact_optional_typed": bounds, "exact_policy_transfer_typed_net": transfer,
            "witness_masks": {"learned": int(BITS[send] | BITS[reply[ask]]),
                              "question_erased": int(BITS[send] | BITS[reply[0]])}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--exact", action="store_true")
    parser.add_argument("--trusted-citations", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.directory, args.exact, args.trusted_citations), indent=2, ensure_ascii=False))
