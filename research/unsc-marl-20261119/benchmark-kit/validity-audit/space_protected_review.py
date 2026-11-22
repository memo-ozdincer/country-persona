"""Review source-licensed protected records and replay the exact routing controls."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

import space_protected_bank as bank
import space_transfer_episode as study
import space_transfer_judge as judge
import space_vote_dates as dates

routing = study.routing
PUBLIC_UNITS = {
    0: ["M", [1], [1]],
    1: ["M", [3, 4], [2]],
    9: ["M", [6], [1, 2]],
}
OMITTED = ["U", [], []]


def records(directory):
    raw = bank.replay(directory)
    answers = {"team-0": {"output": "", "ended": True, "source_ids": list(study.PUBLIC),
                         "input_tokens": 0, "output_tokens": 0}}
    answers.update({k: {"output": r["output"], "ended": r["ended"], "source_ids": r["evidence_ids"],
                        "input_tokens": len(r["input_ids"]), "output_tokens": len(r["output_ids"])}
                    for k, r in raw.items() if k != "may-note"})
    for row in answers.values():
        row["answer"] = "\n\n".join(filter(None, [bank.PUBLIC, row["output"]]))
        row["blind_id"] = sha256(row["answer"].encode()).hexdigest()[:16]
    return answers


def interpret(directory, annotations_path):
    marks = json.loads(annotations_path.read_text())
    assert marks["transcript_sha256"] == study.runner.digest(directory / "transcript.jsonl")
    answers = records(directory)
    assert set(marks["bodies"]) == {row["blind_id"] for key, row in answers.items() if key != "team-0"}
    out = {}
    for key, record in answers.items():
        label = record["blind_id"]
        source_ids = record["source_ids"]
        allowed = {i for i, b in enumerate(study.packet()["evidence"], 1) if b["id"] in source_ids}
        annotation = marks["bodies"].get(label, {"units": {}, "guard": ["C", [], []],
                                                 "reason": "The frozen verified public paragraph."})
        units = {**PUBLIC_UNITS, **{int(k): v for k, v in annotation["units"].items()}}
        assert all(key not in PUBLIC_UNITS for key in map(int, annotation["units"]))
        verdict = {"units": [units.get(k, OMITTED) for k in range(10)], "guard": annotation["guard"]}
        for status, spans, indices in verdict["units"]:
            if status == "M":
                assert set(indices) <= allowed, (key, status, spans, indices)
                assert spans and indices
        scored = judge.interpret(label, record["answer"], verdict)
        date_check = dates.audit(record["answer"], bank.guard.LEDGER)
        words = len(record["output"].split())
        eligible = record["ended"] and words <= bank.BODY_WORDS and scored["score"]["guard"] == "clear"
        eligible = eligible and not date_check["date_conflicts"]
        points = scored["score"]["final"]["lower"]
        out[key] = {**record, **scored, "body_words": words, "eligible": eligible, "points": points,
                    "release_points": points if eligible else 0, "strict_complete": eligible and points == 70,
                    "rationale": annotation["reason"], "date_check": date_check}
    return out


def report(directory, annotations_path, exact):
    bank_scores = interpret(directory, annotations_path)
    fit = json.loads(bank.POLICY.read_text())
    policies = {k: study.as_policy(v) for k, v in fit["policies"].items()}
    priors = {}
    for metric in ("points", "release_points"):
        values = np.array([bank_scores[f"team-{i}"][metric] for i in routing.STATES])
        matrix = routing.receipt_matrix(values, fit["loss"])
        for name, prior in routing.TEST_PRIORS.items():
            best = routing.best_silent(prior, matrix)
            all_arms = {"learned": policies["interactive"], "frozen_independent": policies["independent"],
                        "rubric_planner": policies["exact"], "exact_independent": best,
                        "scripted": routing.scripted()}
            arms = {k: routing.evaluate(p, prior, values, fit["loss"]) for k, p in all_arms.items()}
            arms["request_erased"] = routing.evaluate(policies["interactive"], prior, values, fit["loss"],
                                                      force_missing=True)
            if exact:
                bound, count = routing.exact_optional(prior, matrix, fit["loss"])
                arms["exact_optional"] = {**routing.evaluate(bound, prior, values, fit["loss"]),
                                          "request_maps_examined": count}
                assert arms["exact_optional"]["net"] + 1e-9 >= max(v["net"] for v in arms.values())
            priors.setdefault(name, {})[metric] = arms
    contrasts = {}
    for name, cell in fit["worlds"].items():
        linked = {"interactive": f"team-{cell['interactive']['receipt']}",
                  "independent": f"team-{cell['independent']['receipt']}",
                  "request_erased": f"team-{cell['erased_receipt']}",
                  "full_pool_solo": "solo-7",
                  "receipt_matched_solo_interactive": f"solo-{cell['interactive']['receipt']}",
                  "receipt_matched_solo_independent": f"solo-{cell['independent']['receipt']}"}
        contrasts[name] = {role: {"bank_row": label,
                                  **{k: bank_scores[label][k] for k in ("points", "eligible", "release_points")}}
                           for role, label in linked.items()}
    return {"scope": "Protected procedural rendering with observed receipt writers. Same-assistant unblinded review.",
            "policy_sha256": study.runner.digest(bank.POLICY),
            "annotations_sha256": study.runner.digest(annotations_path), "frozen_public_points": 21,
            "bank": bank_scores, "contrasts": contrasts, "priors": priors}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("inspect", "score"))
    p.add_argument("--directory", type=Path, default=bank.OUT)
    p.add_argument("--annotations", type=Path, default=bank.OUT / "annotations.json")
    p.add_argument("--exact", action="store_true")
    args = p.parse_args()
    if args.mode == "inspect":
        visible = {k: {"id": r["blind_id"], "ended": r["ended"], "words": len(r["output"].split()),
                       "sentences": judge.sentence_rows(r["answer"])} for k, r in records(args.directory).items()}
        print(json.dumps(visible, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(report(args.directory, args.annotations, args.exact), indent=2, ensure_ascii=False))
