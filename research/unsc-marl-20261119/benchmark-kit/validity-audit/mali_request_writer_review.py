"""Score receipt-conditioned Mali records and replay policies against the actual writer."""
import argparse
from itertools import product
import json
from pathlib import Path
import re
import sys

import numpy as np

from mali_request_writer import MALI, ROOT, replay
import mali_source_request_replay as route
from source_record_run import digest
from source_request_policy import BITS, TEST_PRIORS, exact_optional, receipt_matrix, scripted

sys.path.insert(0, str(ROOT / "judge"))
from score import score
sys.path.pop(0)

CITATIONS = re.compile(r"\[[A-Za-z0-9][A-Za-z0-9-]*(?:\s*[,;]\s*[A-Za-z0-9][A-Za-z0-9-]*)*\]")
PRIVATE_RATIONALES = {"france": "french-uae", "russia": "russia"}
LOSS = .10
DOCKET = "The Council voted on S/2023/638 and S/2023/639 on 30 August 2023 at meeting S/PV.9408."


def citations(text):
    return {key for group in CITATIONS.findall(text) for key in re.split(r"\s*[,;]\s*", group[1:-1])}


def score_records(directory, review):
    trace = directory / "transcript.jsonl"
    assert review["transcript_sha256"] == digest(trace)
    request = json.loads(MALI.read_text())
    all_sources = {block["id"]: block for block in request["evidence"]}
    assert "30 August 2023" in request["task"]
    all_sources["docket"] = {"id": "docket", "text": DOCKET}
    rubric = {part["id"]: part for part in request["rubric"]}
    results = []
    outputs = replay(directory)
    assert set(review["records"]) == {r["id"] for r in outputs}
    for mask, row in enumerate(outputs):
        detail = review["records"][row["id"]]
        allowed = set(row["evidence_ids"])
        text = row["output"]
        met = detail["met"]
        assert met.keys() <= rubric.keys()
        units, missing = [], []
        for key in rubric:
            if key not in met:
                units.append({"id": key, "status": "unmet", "response": "", "source": [],
                              "reason": "Incomplete or not licensed by the received evidence."})
                continue
            excerpt, ids = met[key]
            assert set(ids) <= allowed
            assert key not in PRIVATE_RATIONALES or PRIVATE_RATIONALES[key] in ids
            units.append({"id": key, "status": "met", "response": excerpt, "reason": "The exact excerpt meets this criterion.",
                          "source": [{"block": i, "quote": all_sources[i]["text"]} for i in ids]})
            if not set(ids) <= citations(excerpt):
                missing.append(key)
        verdict = {"id": row["id"], "units": units, "guard": detail["guard"]}
        assessor_sources = {*allowed, "docket"}
        assessment = score({**request, "id": row["id"], "evidence": [all_sources[i] for i in sorted(assessor_sources)],
                            "answer": text}, verdict)
        counts = assessment["final"]
        unexpected = sorted(citations(text) - allowed)
        words = len(text.split())
        eligible = row["ended"] and words <= 165 and assessment["guard"] == "clear" and not unexpected
        date_explicit = bool(re.search(r"30 August 2023|2023-08-30|August 30,? 2023", text, re.IGNORECASE))
        objection = detail["retained_france_objection"]
        if objection:
            assert "france-after" in allowed and objection in text
        results.append({
            "mask": mask, "received": row["evidence_ids"], "raw_points": counts["lower"],
            "release_points": counts["lower"] if eligible else 0,
            "eligible": eligible, "ended": row["ended"], "words": words,
            "strict_full_record": eligible and counts["lower"] == 70 and not missing and date_explicit,
            "correct_meeting_date_stated": date_explicit,
            "output_tokens": len(row["output_ids"]), "input_tokens": len(row["input_ids"]),
            "guard": assessment["guard"], "met": sorted(met), "citation_not_in_credited_span": sorted(missing),
            "off_packet_citations": unexpected, "france_objection": objection,
        })
    return results


def policies(policy_path, receipts, decoder_paths):
    learned_record = json.loads(policy_path.read_text())
    learned = tuple(np.asarray(learned_record["training"][k]) for k in ("request", "left_delivery", "reply"))
    settings = {
        "typed": {(f, s): {"truth": f if s in ("full", "reordered") else 0}
                  for f, s in product(range(1, 4), ("full", "reordered", "missing", "reversed"))},
    }
    for name, path in decoder_paths.items():
        decoder = json.loads(path.read_text())
        assert decoder["policy_sha256"] == digest(policy_path)
        settings[name] = {(r["field"], r["variant"]): r for r in decoder["reader"]["readings"]}
    comparisons = []
    for (name, readings), style, (prior_name, prior), measure in product(
        settings.items(), route.STYLES, TEST_PRIORS.items(), ("raw_points", "release_points")
    ):
        views, proof = route.shelf(readings, style, "typed" if name == "typed" else "frozen_model")
        payoff = np.asarray([b[measure] for b in receipts])
        matrix = route.weighted_matrix(prior, views, proof, payoff, LOSS)
        silent = route.best_silent(matrix)
        arms = {k: route.run_policy(policy, prior, views, proof, payoff, LOSS)
                for k, policy in (("learned", learned), ("exact_independent", silent), ("scripted", scripted()))}
        arms["learned_question_erased"] = route.run_policy(learned, prior, views, proof, payoff, LOSS, block_queries=True)
        _, a, b = silent
        assert np.isclose(arms["exact_independent"]["net"],
                          matrix[route.STATES[:, None], route.STATES[None, :], a[:, None], b[None, :, 0]].sum())
        for arm in arms.values():
            assert np.isclose(arm["receipts"][7], 0.)
            distribution = np.asarray(arm["receipts"])
            arm["expected_final_points"] = arm.pop("proof_points")
            arm["release_rate"] = float(distribution @ [r["eligible"] for r in receipts])
            arm["france_objection_retention"] = float(distribution @ [bool(r["france_objection"]) for r in receipts])
        comparisons.append({"reader": name, "style": style, "prior": prior_name, "reward": measure, "arms": arms})
    return comparisons


def report(directory, annotation, policy, old, scoped, run_bound=False):
    data = json.loads(annotation.read_text())
    receipts = score_records(directory, data)
    outcomes = policies(policy, receipts, {"joint_reader": old, "scoped_reader": scoped})
    learner = json.loads(policy.read_text())["training"]
    requested = learner["request"][1]
    own = learner["left_delivery"][1]
    responder = learner["reply"][3]
    with_request = int(BITS[own] | BITS[responder[requested]])
    without_request = int(BITS[own] | BITS[responder[0]])
    optional = {}
    if run_bound:
        from source_request_policy import evaluate

        prior = TEST_PRIORS["uniform"]
        for name in ("raw_points", "release_points"):
            rewards = np.array([r[name] for r in receipts])
            opt, examined = exact_optional(prior, receipt_matrix(rewards, LOSS), LOSS)
            upper = evaluate(opt, prior, rewards, LOSS)
            fixed = next(r for r in outcomes if r["reader"] == "typed" and r["prior"] == "uniform"
                         and r["reward"] == name)
            assert all(z["net"] <= upper["net"] + 1e-9 for z in fixed["arms"].values())
            upper["expected_final_points"] = upper.pop("proof_points")
            optional[name] = {**upper, "request_maps_examined": examined}
    return {
        "scope": data["scope"], "annotations_sha256": digest(annotation),
        "policy_sha256": digest(policy), "decoder_sha256": {"joint": digest(old), "scoped": digest(scoped)},
        "loss": LOSS, "records": receipts, "comparisons": outcomes, "exact_optional_typed_uniform": optional,
        "intact_link_witness": {
            "left_available": [1], "right_available": [1, 2], "requested": requested,
            "learned_receipt": with_request, "question_erased_receipt": without_request,
            "learned_record": receipts[with_request], "record_with_request_erased": receipts[without_request],
        },
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    cli.add_argument("annotations", type=Path)
    cli.add_argument("policy", type=Path)
    cli.add_argument("joint_reader", type=Path)
    cli.add_argument("scoped_reader", type=Path)
    cli.add_argument("--exact", action="store_true")
    args = cli.parse_args()
    print(json.dumps(report(args.directory, args.annotations, args.policy, args.joint_reader, args.scoped_reader, args.exact),
                     indent=2, ensure_ascii=False))
