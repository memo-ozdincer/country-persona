"""Freeze and compare excerpt and whole-note forecasts on Resolution 2422."""
import csv
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(HERE.parent))
import facilitator_silence_joint_fit as study

D, fit, joint, R = study.D, study.fit, study.joint, study.R
spec = importlib.util.spec_from_file_location("budget_reference", HERE.parent / "haiti2466-budget-transfer/plan.py")
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)


def provenance(packet):
    event = packet["event"]
    read = study.budget.read
    ub = read(ROOT / "data/manifests/unbench-full-20260926.json")
    us = read(ROOT / "data/manifests/unsc-bench-20260926.json")
    data = ROOT / us["local_root"] / "adopted/data.parquet"
    digest = sha256(data.read_bytes()).hexdigest()
    assert digest == next(f["sha256"] for f in us["files"] if f["path"] == "adopted/data.parquet")
    row, = pq.ParquetFile(data).read().slice(event["unsc_bench_adopted_index"], 1).to_pylist()
    assert (row["identifiers"]["symbol"], row["meeting"]["meeting_record"],
            row["draft_from_file1"]["draft_symbol"], row["dates"]["vote_date"]) == (
                event["resolution"], event["meeting"], event["draft"], event["date"])
    assert row["urls_meeting"]["en"] == packet["official"]["meeting"]
    assert row["urls_resolution"]["en"] == packet["official"]["resolution"]
    folder = ROOT / ub["extraction_root"]
    found = {}
    for split in ("train", "test"):
        with (folder / f"task2_{split}_author.csv").open(encoding="utf-8-sig", newline="") as stream:
            found[split] = [(i, r) for i, r in enumerate(csv.DictReader(stream)) if r["Original_id"] == event["unbench"]]
    assert not found["train"] and len(found["test"]) == 15
    assert {r["Date"] for _, r in found["test"]} == {event["date"]}
    votes = {r["Country"]: r["Voting"] for _, r in found["test"]}
    assert votes == {r["name"]: r["vote"] for r in row["member_state_votes"]}
    assert {n for n, v in votes.items() if v != "Y"} == {"RUSSIAN FEDERATION"}
    assert votes["RUSSIAN FEDERATION"] == "A" and "SERBIA" not in votes
    drafts = list((folder / "drafts_adopted" / event["unbench"]).glob("*.json"))
    draft, = drafts
    assert draft.name == f'{event["draft"].replace("/", "_")}-EN.json'
    return {"unbench_test_rows": [i for i, _ in found["test"]], "votes": votes,
            "unbench_draft_sha256": sha256(draft.read_bytes()).hexdigest(), "unsc_bench_sha256": digest}


def compare(public, whole, prior, original, model):
    left, right = study.opening(public, prior, original)
    mass = joint.opening(left, right, prior)
    q, reply = study.tail(public, mass, model)
    teams = {
        "learned": (q, reply),
        "same_responder_silence": (np.zeros_like(q), reply),
        "exact_silence": fit.exact(public, mass, fit.PERFECT, independent=True),
        "whole_planner": fit.exact(whole, mass, fit.PERFECT),
        "excerpt_planner": fit.exact(public, mass, fit.PERFECT),
    }
    for card in range(1, 4):
        teams[f"fixed_{card}"] = np.where(D.CHAIR_LEGAL[:, card], card, 0), reply
    result = {}
    for arm, (question, responder) in teams.items():
        scores = joint.metric((left, right, question, responder), prior, public, fit.PERFECT)
        result[arm] = {**scores, "request_map": question.tolist()}
    exact = result["excerpt_planner"]["net"]
    assert all(row["net"] <= exact + 1e-10 for row in result.values())
    return {"openers": [left.tolist(), right.tolist()], "arms": result}


def run():
    packet_path = HERE / "packet.json"
    packet = study.budget.read(packet_path)
    deployed = study.EVIDENCE / "results.json"
    model = study.budget.read(deployed)["fit"]["response_aware"]
    original = study.budget.read(study.OLD)["training"]["budget_fit"]
    result = {}
    for cap in packet["limits"]:
        public, costs = reference.bank(packet, cap, whole=False)
        whole, _ = reference.bank(packet, cap, whole=True)
        assert np.all(public >= whole)
        result[str(cap)] = {
            "excerpt_scores": public.tolist(), "whole_scores": whole.tolist(), "excerpt_words": costs,
            "laws": {law: compare(public, whole, prior, original, model) for law, prior in R.TEST_PRIORS.items()},
        }
    files = (Path(__file__), packet_path, HERE / "protocol.md", Path(reference.__file__), deployed, study.OLD)
    return {"event": packet["event"], "provenance": provenance(packet), "budgets": result,
            "sha256": {str(p.relative_to(study.HERE)): sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
