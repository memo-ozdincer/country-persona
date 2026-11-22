"""Execute the paired Somalia witness with fresh, role-scoped passage generation."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import match as k
import numeric_control as wire

q, n, a, o, r, t, D = k.q, k.n, k.a, k.o, k.r, k.t, k.D
e, BITS = k.e, k.BITS
OUT = HERE / "evidence"
LIMIT = 6
ARMS = ("interval_team", "query_erased", "interval_fixed", "fixed_us")


def settings():
    docket = n.read(t.SOURCE)
    roles = docket["roles"]
    scores = n.read(t.HERE / "numeric-results.json")["score_banks"]["native"]
    bank = np.array(scores)
    scenario = n.read(t.HERE / "numeric-results.json")["dispatcher_witnesses"]["asymmetric"]
    world = tuple(scenario["world"])
    delivery = tuple(scenario["delivery"])
    assert scenario["routes"]["interval_team"]["query"] == 3
    assert scenario["routes"]["interval_fixed"]["query"] == 1
    law, _ = a.laws()["asymmetric"]
    opener = n.read(o.replan.study.OLD)["training"]["budget_fit"]
    openings = o.replan.study.opening(r.f.views(bank)["4"], law, opener)
    mass = o.opening(*openings, law)
    calibration = {i: bank[i] for i in range(7) if i != 3}
    choices = r.evaluate_locked(calibration, bank[3], law, openings, mass, {})
    active = choices["interval_team"][1]
    fixed_us = (np.where(D.CHAIR_LEGAL[:, 3], 3, 0), active[1])
    teams = {"interval_team": active, "query_erased": active,
             "interval_fixed": choices["interval_fixed"][1], "fixed_us": fixed_us}
    return docket, roles, world, delivery, openings, teams


def request(docket, role, phase, inventory, earlier, heard):
    role_index = docket["roles"]
    payload = {"task": docket["task"], "speaker": role, "stage": phase,
               "private_inventory": [name for name, bit in zip(role_index, BITS[1:]) if inventory & bit],
               "earlier_attempt": role_index[earlier - 1] if earlier else None,
               "heard_question": role_index[heard - 1] if heard else None,
               "passages": docket["menus"][role]}
    instructions = (
        "Select passage IDs that preserve this speaker's distinct position. " + docket["prompts"][role]
        + " Return only a JSON array of ID strings ordered by importance. Omit merely secondary detail."
    )
    return t.LIB.b.request(instructions, payload, 72)


def simulate(generate):
    docket, roles, world, delivery, openings, teams = settings()
    cache = {}
    private = {}

    def attempt(card, desk, stage, prior_send, heard, arrival):
        if not card:
            return None
        assert BITS[card] & world[desk]
        role = roles[card - 1]
        prompt = request(docket, role, stage, world[desk], prior_send, heard)
        key = e.checksum(prompt)
        reused = key in cache
        if not reused:
            assert len(cache) < LIMIT
            cache[key] = generate(prompt)
        row = {"part": role, "response": cache[key]}
        selected, status = wire.normalize(row, docket["menus"])
        return {"card": card, "role": role, "sent": selected, "status": status,
                "delivered": bool(arrival and selected), "request": prompt, "reused": reused,
                "response": cache[key]}

    op1, op2 = (int(v[mask]) for v, mask in zip(openings, world))
    common = [attempt(op, desk, "opening", 0, 0, delivery[desk]) for desk, op in enumerate((op1, op2))]
    for row in common:
        if row and row["delivered"]:
            private[row["role"]] = row["sent"]
    common_mask = sum(bit for bit, role in zip(BITS[1:], roles) if role in private)
    traces = {}
    spans = t.plan()["spans"]
    for arm in ARMS:
        chair, response = teams[arm]
        query = int(chair[common_mask])
        heard = query if delivery[2] and arm != "query_erased" else 0
        reply = int(response[world[1], op2, heard])
        follow = attempt(reply, 1, "reply", op2, heard, delivery[3])
        admitted = dict(private)
        if follow and follow["delivered"]:
            admitted[follow["role"]] = follow["sent"]
        receipt = sum(bit for bit, role in zip(BITS[1:], roles) if role in admitted)
        read = {role: admitted.get(role, []) for role in roles}
        output = q.render(docket, spans, read, receipt)
        cost = float(D.SEND_COST[op1] + D.SEND_COST[op2] + D.QUERY_COST[query] + D.SEND_COST[reply])
        traces[arm] = {"opening_mask": common_mask, "query": query, "heard": heard,
                       "reply": reply, "delivery": follow, "receipt": receipt, "cost": cost, "record": output}
    return {"world": world, "opening": common, "arms": traces, "physical_calls": len(cache)}


def plan():
    gold = n.read(HERE.parent / "numeric-grades.json")["selection"]
    prompts = []

    def generate(request):
        prompts.append(request)
        speaker = json.loads(request["messages"][-1]["content"])["speaker"]
        return {"text": json.dumps(gold[speaker][0]), "termination": "complete"}

    routes = simulate(generate)
    pinned = (Path(__file__), HERE / "protocol.md", HERE / "matches.json", t.SOURCE,
              HERE.parent / "numeric-results.json", HERE.parent / "numeric-grades.json", Path(wire.__file__))
    return {"ideal_physical_requests": prompts,
            "ideal_receipts": {k: r["receipt"] for k, r in routes["arms"].items()},
            "sha256": {f.name: sha256(f.read_bytes()).hexdigest() for f in pinned}}


def collect(generate, folder):
    assert plan() == n.read(HERE / "plan.json")

    def record(prompt):
        output = generate(prompt)
        n.base.suite.append(folder / "calls.jsonl", {"request": prompt, "response": output})
        return output

    output = simulate(record)
    (folder / "dispatch.json").write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")


def calls():
    return n.lines(OUT / "calls.jsonl")


def verify():
    assert plan() == n.read(HERE / "plan.json")
    with patch.object(n, "OUT", OUT), patch.object(t.LIB.audit, "calls", calls):
        receipts = t.LIB.audit.verify()
    sequence = iter(calls())

    def replay(request):
        row = next(sequence)
        assert request == row["request"]
        return row["response"]

    rebuilt = json.loads(json.dumps(simulate(replay)))
    assert rebuilt == n.read(OUT / "dispatch.json")
    assert next(sequence, None) is None
    return receipts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    if mode == "run":
        with patch.object(n.base.suite, "collect", collect), patch.object(
                n.base, "roster", return_value={"matched-somalia-live-transport": None}):
            n.base.run(OUT)
    else:
        e.emit(plan() if mode == "plan" else verify())
