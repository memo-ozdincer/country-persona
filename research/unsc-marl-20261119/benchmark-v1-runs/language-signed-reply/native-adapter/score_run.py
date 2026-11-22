"""Score native action changes and the corresponding one-question replays."""
import json
from pathlib import Path
import sys

import torch

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
sys.path.insert(0, str(PARENT))
import fit as old_fit
import cases
import local_guard

assert old_fit.HERE == PARENT
E = cases.E
COST_QUERY = .06


def records():
    return [json.loads(line) for line in (HERE / "evidence/scores.jsonl").read_text().splitlines()]


def native_logits(rows):
    vectors = {label: torch.tensor([r[label] for r in rows], dtype=old_fit.DTYPE)
               for label in ("frozen", "adapted")}
    _, h, old, _ = old_fit.observations()
    prior = E.read(PARENT / "results.json")["weights"]
    weights = torch.tensor(prior["residual"], dtype=old_fit.DTYPE)
    vectors["previous_feature_head"] = old + h @ weights
    vectors["previous_frozen_capture"] = old
    return vectors


def controller_records(held):
    original = E.read(PARENT / "joint/results.json")["held"]
    roster = {row["id"]: row for row in cases.held()}
    rows = []
    for state in original:
        states = {}
        for chair in ("public_value_exact_reply", "learned_chair_exact_reply"):
            choice = state["arms"][chair]["choice"]
            for actor in ("frozen", "adapted", "previous_feature_head", "exact"):
                for verify in ("raw", "local_check"):
                    key = f"{chair}/{actor}/{verify}"
                    base = 1. if state["mode"] == "certified" else .15
                    if not choice:
                        states[key] = {"utility": base, "proof_probability": 0., "wrong": 0, "sent": 0}
                        continue
                    if state["mode"] == "two_openings":
                        row_id = state["key"] + "/" + str(choice-1)
                    else:
                        row_id = state["key"]
                    item = roster[row_id]
                    expect = item["audit"]
                    raw = held[row_id]["arms"][actor]["selected"]
                    sign = local_guard.signature(item)
                    action = "P" if verify == "local_check" and raw not in {"P", sign} else raw
                    outcome = expect[action]
                    probability = state["rates"][choice-1]
                    net = base + (.85*probability if outcome["new_proof"] else 0.)
                    if not outcome["truthful"]:
                        net = -1.
                    states[key] = {"utility": net - COST_QUERY - cases.COST*(action != "P"),
                                   "proof_probability": probability if outcome["new_proof"] else 0.,
                                   "wrong": int(outcome["wrong_commit"]), "sent": int(action != "P")}
                    if actor == "exact":
                        assert abs(states[key]["utility"] - state["arms"][chair]["net"]) < 1e-10
        rows.append({"key": state["key"], "rate": state["rates"], "controllers": states})
    return {"presentations": len(rows), "totals": {k: {
                "mean_net": sum(row["controllers"][k]["utility"] for row in rows)/len(rows),
                "expected_proofs": sum(row["controllers"][k]["proof_probability"] for row in rows),
                "wrong_commitments_if_delivered": sum(row["controllers"][k]["wrong"] for row in rows),
                "sent": sum(row["controllers"][k]["sent"] for row in rows)}
            for k in rows[0]["controllers"]}, "rows": rows}


def run():
    data = records()
    roster = cases.roster()
    world = [x for rows in roster.values() for x in rows]
    assert [row["id"] for row in data] == [f'{split}/{r["id"]}' for split, content in roster.items() for r in content]
    assert [row["utility"] for row in data] == [x["utility"] for x in world]
    vectors = native_logits(data)
    n = len(roster["train"])
    scores = {}
    for split, selection in (("train", slice(0,n)), ("held", slice(n,None))):
        reply = old_fit.review(roster[split], {key: value[selection] for key, value in vectors.items()})
        scores[split] = {"summary": old_fit.aggregate(reply), "rows": reply}
    controller = controller_records(scores["held"]["rows"])
    by_file = (Path(__file__), HERE / "evidence/scores.jsonl", PARENT / "joint/results.json")
    return {"results": scores, "controller": controller,
            "sha256": {p.name: old_fit.digest(p) for p in by_file}}


if __name__ == "__main__":
    E.emit(run())
