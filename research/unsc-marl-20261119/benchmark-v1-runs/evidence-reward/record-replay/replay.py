"""Compose policy selections and receipt branches into final-record score packets."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

import render
import followup as f
import value_fit as value
from run_suite import verify_release

env, e = render.env, render.e
HERE = Path(__file__).resolve().parent
RATES = (.20, .55, .80)
ARMS = ("no_followup", "joint", "value")


def archive():
    rows = e.read(env.RUNS / "source-bound-chair/replay.json")["records"]
    complete = {}
    for key, row in rows.items():
        name = key.split("/")[0]
        for d in row["declarations"]:
            assert complete.setdefault((name, d["role"]), d["requirement"]) == d["requirement"]
    return complete


def select(mode, state, rate, joint_heads, value_heads):
    if state["decision"] == "U" or mode == "no_followup":
        return None, False
    if mode == "value":
        role = value.choose(state, rate, env.ASK, f.FEE, value_heads)
        return role, bool(role)
    _, p, respond, _ = f.components(state, rate, joint_heads)
    pick = max(range(3), key=p.__getitem__)
    return (None, False) if pick == 0 else (env.ROLES[pick-1], respond[pick-1] > .5)


def variants(row, stimulus, case, complete, rate, mode, joint, heads):
    data = json.loads(stimulus["messages"][1]["content"])
    original = env.old.initial(data["public_claims"])
    packet = render.BASE.project(case)
    assert env.state(packet["options"], original) == row["before"]
    for state, weight, _, cost in f.start_states(row, False):
        signs = list(original)
        if state != row["before"]:
            # The environment knows the local truth only to produce the sign.
            compatible = env.options(packet["options"], row["truth"]["sign"])
            signs.append(env.old.claim("first:reply", row["named"],
                                      stimulus["target"] in compatible, stimulus["target"]))
        assert env.state(packet["options"], signs) == state
        role, send = select(mode, state, rate, joint, heads)
        cost += env.ASK * bool(role) + f.FEE * send
        if not send:
            yield weight, cost, bool(role), False, render.final(packet, signs, {})
            continue
        role_name = dict(zip(env.ROLES, packet["roles"], strict=True))[role]
        claim = complete[case["id"], role_name]
        assert render.BASE.filter_local(packet["options"], {"requirement": claim},
                                        case["membership"][case["roles"].index(role_name)])
        req = next(iter(claim.items()))
        yield weight * (1-rate), cost, True, True, render.final(packet, signs, {})
        yield weight * rate, cost, True, True, render.final(packet, signs, {role: req})


def replay(rates=RATES, value_heads=None):
    version = verify_release()
    cases = e.cases()
    stimuli = {r["id"]: r for r in e.read(env.old.SIGNED/"roster.json")["held"]}
    held = [r for split, r in env.records() if split == "held"]
    complete = archive()
    joint = e.read(HERE.parent/"followup.json")["fit"]["heads"]
    heads = e.read(HERE.parent/"value-fit.json")["heads"] if value_heads is None else value_heads
    packets, paths = {}, {}
    for rate in rates:
        paths[str(rate)] = output = {}
        for row in held:
            key = row["id"]
            case = cases[key.split("/")[0]]
            output[key] = bundles = {}
            for mode in ARMS:
                bundles[mode] = rows = []
                for probability, cost, question, send, final in variants(
                    row, stimuli[key], case, complete, rate, mode, joint, heads
                ):
                    packet = e.final_packet(case, [{}, {}, {"text": final["text"]}])
                    packets[packet["id"]] = packet
                    rows.append({"id": packet["id"], "probability": probability, "cost": cost,
                                 "question": question, "send": send, "record": final})
                assert abs(sum(r["probability"] for r in rows) - 1.) < 1e-9
    assert len(held) == 44
    files = (Path(__file__), HERE/"protocol.md", HERE/"render.py", HERE.parent/"followup.json",
             HERE.parent/"value-fit.json", env.old.SIGNED/"roster.json", e.HERE/"release.json")
    return {"version": version, "packets": [packets[i] for i in sorted(packets)], "paths": paths,
            "sha256": {str(p.relative_to(render.BASE.ROOT)): sha256(p.read_bytes()).hexdigest() for p in files}}


def score(data, marks):
    cases = e.cases()
    packets = {p["id"]: p for p in data["packets"]}
    assert set(marks) == set(packets)
    results = {}
    for rate, episodes in data["paths"].items():
        sums = {mode: Counter() for mode in ARMS}
        graded = {}
        for key, arms in episodes.items():
            case = cases[key.split("/")[0]]
            for mode, paths in arms.items():
                tally = sums[mode]
                for row in paths:
                    pid = row["id"]
                    answer = packets[pid]["answer"]
                    if pid not in graded:
                        graded[pid] = e.final_score(case, [{}, {}, {"text": answer, "termination": "complete"}],
                                                    marks[pid])
                    grade = graded[pid]
                    weight = row["probability"]
                    tally["exact"] += weight * grade["mechanical"]["accepted"]
                    tally["released_70"] += weight * grade["released_70"]
                    tally["raw_lower_70"] += weight * grade["raw_70"][0]
                    tally["strict"] += weight * grade["strict"]
                    tally["cost"] += weight * row["cost"]
                    tally["followup_questions"] += weight * row["question"]
                    tally["net"] += weight * (grade["released_70"]/70 - row["cost"])
        results[rate] = {"arms": sums, "unique_grades": graded}
    return {"annotation": "same-assistant, deterministic final records",
            "presentations": len(next(iter(data["paths"].values()))), "rates": results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("replay", "deck", "score"))
    selected = parser.parse_args().mode
    result = replay()
    if selected == "score":
        result = score(result, e.read(HERE/"marks.json"))
    elif selected == "deck":
        result = result["packets"]
    e.emit(result)
