"""Replay the frozen router with source-verified national clauses instead of prose notes."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import unifil_final_review as review

study, judge = review.study, review.judge
TEXT = {
    "brazil": "Brazil said the French text kept UNIFIL free to operate and addressed some of Lebanon's concerns.",
    "china": "China said the text fell short on Lebanon's concerns and emphasized sovereignty and consent in peacekeeping.",
    "russia": "Russia abstained over late changes that lost an earlier compromise, while still supporting UNIFIL's work.",
}
COMPARISON = ("Brazil and China both supported the mission. "
              "They differed on how adequately the text addressed Lebanon's concerns.")


def records(directory, annotations):
    result = dict(review.grade(directory, annotations))
    for mask in range(8):
        selected = [s for i, s in enumerate(study.FIELDS) if mask & (1 << i)]
        parts = [TEXT[k] for k in selected]
        units = dict(review.PUBLIC)
        for idx, role in enumerate(study.FIELDS):
            if role in selected:
                units[5 + idx] = ["M", [5 + selected.index(role)], [3 + idx]]
        if mask & 3 == 3:
            parts.append(COMPARISON)
            start = 5 + len(selected)
            units[8] = ["M", [start], [3, 4]]
            units[9] = ["M", [5, 6, start + 1], [3, 4]]
        body = "\n\n".join(parts)
        answer = "\n\n".join(filter(None, [study.PUBLIC, body]))
        allowed = [*study.PUBLIC_IDS, *selected]
        for idx, mark in units.items():
            if idx in review.DEPENDENCIES:
                assert review.DEPENDENCIES[idx] <= set(mark[2])
        assert len(body.split()) <= study.BODY_WORDS
        packet = [units.get(i, ["U", [], []]) for i in range(10)]
        verdict = {"units": packet, "guard": ["C", [], []]}
        with patch.object(judge.study, "packet", study.packet):
            assessed = judge.interpret(f"verified-{mask}", answer, verdict)
        points = assessed["score"]["final"]["lower"]
        result[f"team-{mask}"] = {**assessed, "answer": answer, "source_ids": allowed, "points": points,
                                  "eligible": True, "release_points": points, "body_words": len(body.split()),
                                  "strict_complete": points == 70}
    return result


def report(directory, exact):
    annotation = directory / "annotations.json"
    scored = records(directory, annotation)
    with patch.object(review, "grade", return_value=scored):
        result = review.report(directory, annotation, exact)
    return {**result, "scope": "Retrospective record assembly from author-verified national clauses. "
            "The original Qwen solo records appear as separate reference controls. No new model generation.",
            "compiler_sha256": study.common.runner.digest(Path(__file__)),
            "prose_score_sha256": study.common.runner.digest(directory / "score.json")}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--directory", type=Path, default=study.OUT)
    cli.add_argument("--exact", action="store_true")
    args = cli.parse_args()
    print(json.dumps(report(args.directory, args.exact), indent=2, ensure_ascii=False))
