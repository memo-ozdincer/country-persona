"""Build first-stage action values from final coverage and modeled follow-up."""
import json
from hashlib import sha256
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
RECORD = HERE.parent / "record-replay"
sys.path.insert(0, str(RECORD))
import render

env, E = render.env, render.e
ACTIONS = ("Y", "N", "P")


def supported_record(state, delivery, before_points, complete_points):
    """Return final point coverage, expected downstream fee, and extra requests."""
    if state["decision"] == "U":
        return [0., 0., 0.]
    if state["known"] == 2:
        return [complete_points, 0., 0.]
    fee = env.ASK + env.COSTS["mandate_target"]
    gain = delivery * (complete_points - before_points) / 70
    if state["known"] == 1 and gain > fee + 1e-10:
        return [before_points + delivery * (complete_points - before_points), fee, 1.]
    return [before_points, 0., 0.]


def summarize_delivery(before, after, delivery, send_cost):
    return [delivery * a + (1-delivery) * b + (send_cost if i == 1 else 0.)
            for i, (a, b) in enumerate(zip(after, before, strict=True))]


def run():
    signed = env.old.SIGNED
    roster = E.read(signed/"roster.json")
    deck = E.read(RECORD/"deck.json")
    marks = E.read(RECORD/"marks.json")
    live = E.read(RECORD/"live/schema/results.json")["clarified"]["results"]
    cases = E.cases()
    reviewed = {(p["id"], p["answer"]): marks[p["id"]] for p in deck}
    # The synthetic payout uses the published rubric, not the held marks.
    weights = {unit["weight"] for case in cases.values() if case["track"] == "workshop"
               for unit in case["rubric"] if unit["id"] == "positions"}
    assert len(weights) == 1
    full = 70.
    partial = full - weights.pop()
    paths = {}

    def verify_held(item, after_log, pay):
        case = cases[item["id"].split("/")[0]]
        packet = render.BASE.project(case)
        final = render.final(packet, after_log, {})
        calls = [{}, {}, {"text": final["text"], "termination": "complete"}]
        pid = E.final_packet(case, calls)["id"]
        verdict = reviewed.get((pid, final["text"]))
        if verdict is None:
            return {"id": pid, "unreviewed": final["text"], "record": final}
        score = E.final_score(case, calls, verdict)
        if pay[2]:
            followup = live[item["id"]]
            assert followup["admitted"] and followup["before"]["released_70"] == score["released_70"]
            expected = score["released_70"] + item["delivery"] * (
                followup["after"]["released_70"] - score["released_70"])
        else:
            expected = score["released_70"]
        assert abs(expected - pay[0]) < 1e-8
        return {"id": pid, "released_without_followup": score["released_70"]}

    for split, items in roster.items():
        prepared = paths.setdefault(split, {})
        for item in items:
            key = item["id"]
            local = json.loads(item["messages"][1]["content"])
            menu = (env.menu_from_synthetic(local["possible_packages"]) if split == "train"
                    else cases[key.split("/")[0]]["options"])
            log = env.old.initial(local["public_claims"])
            before = env.state(menu, log)
            truth = "Y" if item["truth"] else "N"
            valid = env.old.claim("first:reply", local["you"], truth == "Y", item["target"])
            after_log = log + [valid]
            after = env.state(menu, after_log)
            assert after["decision"] == item["audit"][truth]["decision"]
            p_before = supported_record(before, item["delivery"], partial, full)
            p_after = supported_record(after, item["delivery"], partial, full)
            sent = summarize_delivery(p_before, p_after, item["delivery"], .035)
            wrong = [p_before[0], p_before[1]+.035, p_before[2]]
            columns = {truth: sent, "P": p_before, "N" if truth == "Y" else "Y": wrong}
            reward = [(-1.035 if a not in {truth, "P"} else columns[a][0]/70 - columns[a][1])
                      for a in ACTIONS]
            check = {
                "truthful": verify_held(item, after_log, p_after),
                "silent": verify_held(item, log, p_before),
            } if split == "held" else {}
            prepared[key] = {"truthful_action": truth, "reward": reward, "guarded_outcome": columns,
                             "review": check, "first_proof_if_delivered": item["audit"][truth]["new_proof"],
                             "live_followup_context": key in live, "followup_if_delivered": p_after[2]}
    files = (Path(__file__), HERE/"protocol.md", RECORD/"marks.json", RECORD/"deck.json",
             RECORD/"live/schema/results.json", signed/"roster.json")
    return {"positions_points": full - partial, "paths": paths,
            "sha256": {str(p.relative_to(env.CHAIR.ROOT)): sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    E.emit(run())
