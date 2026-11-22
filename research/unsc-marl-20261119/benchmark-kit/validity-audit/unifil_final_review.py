"""Score exact spans and compare the transferred UNIFIL router with exact alternatives."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import space_protected_review as controls
import space_transfer_judge as judge
import unifil_final_transfer as study

routing = study.common.routing
PUBLIC = {
    0: ["M", [1], [1]],
    1: ["M", [2], [1]],
    2: ["M", [3], [2]],
    3: ["M", [4], [2]],
    4: ["M", [4], [2]],
}
DEPENDENCIES = {5: {3}, 6: {4}, 7: {5}, 8: {3, 4}, 9: {3, 4}}


def records(directory):
    rows = study.replay(directory)
    public = {"output": "", "ended": True, "evidence_ids": list(study.PUBLIC_IDS),
              "input_ids": [], "output_ids": []}
    records = {}
    for key, row in {"team-0": public, **{k: v for k, v in rows.items() if not k.startswith("note-")}}.items():
        answer = "\n\n".join(filter(None, [study.PUBLIC, row["output"]]))
        records[key] = {"answer": answer, "blind_id": sha256(answer.encode()).hexdigest()[:16],
                        "output": row["output"], "ended": row["ended"], "source_ids": row["evidence_ids"],
                        "input_tokens": len(row["input_ids"]), "output_tokens": len(row["output_ids"])}
    return records


def grade(directory, annotation):
    answers = records(directory)
    labels = json.loads(annotation.read_text())
    assert labels["transcript_sha256"] == study.common.runner.digest(directory / "transcript.jsonl")
    assert set(labels["bodies"]) == {r["blind_id"] for k, r in answers.items() if k != "team-0"}
    result = {}
    for role, row in answers.items():
        ident = row["blind_id"]
        given = {i for i, s in enumerate(study.packet()["evidence"], 1) if s["id"] in row["source_ids"]}
        mark = labels["bodies"].get(ident, {"units": {}, "guard": ["C", [], []], "reason": "Only verified procedure."})
        private = {int(k): x for k, x in mark["units"].items()}
        assert private.keys() <= DEPENDENCIES.keys()
        for i, (status, _, sources) in private.items():
            if status == "M":
                assert DEPENDENCIES[i] <= set(sources) <= given
        units = {**PUBLIC, **private}
        verdict = {"units": [units.get(i, ["U", [], []]) for i in range(10)], "guard": mark["guard"]}
        with patch.object(judge.study, "packet", study.packet):
            scored = judge.interpret(ident, row["answer"], verdict)
        words = len(row["output"].split())
        eligible = row["ended"] and words <= study.BODY_WORDS and scored["score"]["guard"] == "clear"
        result[role] = {**row, **scored, "body_words": words, "eligible": eligible,
                        "points": scored["score"]["final"]["lower"],
                        "release_points": scored["score"]["final"]["lower"] if eligible else 0,
                        "strict_complete": eligible and scored["score"]["strict"], "rationale": mark["reason"]}
    return result


def report(directory, annotations, exact):
    scores = grade(directory, annotations)
    with patch.object(controls, "interpret", return_value=scores):
        report = controls.report(directory, annotations, exact)
    # Optimize a public-rubric transfer policy assuming every licensed claim is realized.
    # This planner never consumes ratings from the generated UNIFIL records.
    intended = routing.points({"weights": (7, 7, 7), "joint": (3, 14)})
    loss = routing.TRAIN_LOSS
    ideal, count = routing.exact_optional(routing.TEST_PRIORS["uniform"], routing.receipt_matrix(intended, loss), loss)
    for name, prior in routing.TEST_PRIORS.items():
        for metric in ("points", "release_points"):
            payoff = np.array([scores[f"team-{i}"][metric] for i in routing.STATES])
            report["priors"][name][metric]["public_rubric_unifil_planner"] = routing.evaluate(ideal, prior, payoff, loss)
    return {**report, "scope": "Separate UNIFIL source family. Frozen Outer Space fit, typed simulated receipts, "
            "and same-assistant unblinded assessments of new writer outputs.",
            "frozen_public_points": 35, "intended_private_scores": intended.tolist(),
            "case_rubric_planner_maps_examined": count,
            "case_rubric_plan": [p.tolist() for p in ideal]}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("inspect", "score"))
    cli.add_argument("--directory", type=Path, default=study.OUT)
    cli.add_argument("--exact", action="store_true")
    args = cli.parse_args()
    if args.mode == "inspect":
        print(json.dumps({k: {"id": r["blind_id"], "ended": r["ended"], "words": len(r["output"].split()),
                              "sentences": judge.sentence_rows(r["answer"])}
                          for k, r in records(args.directory).items()}, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(report(args.directory, args.directory / "annotations.json", args.exact),
                         indent=2, ensure_ascii=False))
