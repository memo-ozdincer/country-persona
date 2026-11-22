"""Execute one selected learned historical route with fresh exact-source receipts."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import qualify as selector

o, e = selector.o, selector.e
h, D = o.h, o.D
ROOT = h.ARCHIVE.parents[2]
RUN = HERE / "evidence"
CASE_PATH = ROOT / "crossbench/unifil-record.json"
BANK_PATH = HERE.parent / "quality-results.json"
NAMES = ("none", "brazil", "china", "russia")
ARMS = ("learned", "erased", "no_request", "fixed")
LIMIT = 6


def model_inputs():
    case = e.read(CASE_PATH)
    points = selector.cases.banks()["unifil"]
    initial = e.read(o.replan.study.OLD)["training"]["budget_fit"]
    params = tuple([np.array(row) for row in e.read(path)["parameters"]]
                   for path in (HERE.parents[1] / "fit.json", HERE.parent / "sparse-results.json"))
    return case, points, initial, params


def solve():
    _, points, initial, params = model_inputs()
    estimated = selector.cases.singleton(points)
    previous = e.read(BANK_PATH)["conditions"]["unifil"]
    label = next(name for name in o.R.TEST_PRIORS if previous[name]["policy"] in ("dense", "sparse"))
    law = o.R.TEST_PRIORS[label]
    openers = o.replan.study.opening(estimated, law, initial)
    coords = tuple(float(points[k]) for k in (0, 1, 2, 4))
    _, candidates, predicted, _ = selector.choose(coords, openers, law, params)
    floor = predicted["quiet"]["released"]
    valid = [name for name in candidates if predicted[name]["released"] >= floor - 1e-10]
    learned = max(valid, key=lambda arm: (predicted[arm]["net"], arm == "quiet"))
    assert learned == previous[label]["policy"] and learned in ("dense", "sparse")
    fixed = max((f"fixed_{i}" for i in range(1, 4)), key=lambda name: predicted[name]["net"])
    policies = {"learned": candidates[learned], "erased": candidates[learned],
                "no_request": candidates["quiet"], "fixed": candidates[fixed]}
    return points, label, law, learned, fixed, openers, policies


def request(case, desk, card, received, heard):
    chosen = next(x for x in case["evidence"] if x["id"] == NAMES[card])
    payload = {
        "desk": desk, "card": chosen["id"], "evidence": chosen["text"],
        "publicly_received_cards": [NAMES[i] for i in range(1, 4) if received & (1 << (i - 1))],
        "heard_question": NAMES[heard],
    }
    return {"messages": [
        {"role": "system", "content": "Return one JSON object with keys card and quote. "
         "Use the given card ID and copy the entire evidence text exactly. Copy no other text."},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}], "max_output_tokens": 160}


def bit(card):
    assert 0 <= card < 4
    return 0 if card == 0 else 1 << (card - 1)


def ideal(_request):
    data = json.loads(_request["messages"][-1]["content"])
    return {"text": json.dumps({"card": data["card"], "quote": data["evidence"]}, ensure_ascii=False),
            "termination": "complete"}


def validate(reply, req):
    got = h.r.parse(reply)
    given = json.loads(req["messages"][-1]["content"])
    return set(got) == {"card", "quote"} and got["card"] == given["card"] and got["quote"] == given["evidence"]


def simulate(context, inventory, generate):
    case = model_inputs()[0]
    _, _, _, _, _, openers, policies = context
    left, right = inventory
    cache = {}

    def activate(desk, card, owned, public_mask, heard):
        if not card:
            return 0, None
        assert owned & bit(card), (desk, owned, card)
        req = request(case, desk, card, public_mask, heard)
        key = e.checksum(req)
        if key not in cache:
            if len(cache) >= LIMIT:
                raise ValueError("Distinct native-call cap exceeded")
            reply = generate(req)
            cache[key] = reply
            reused = False
        else:
            reply, reused = cache[key], True
        admit = validate(reply, req)
        return (bit(card) if admit else 0), {"stage": desk, "card": NAMES[card], "request": req, "response": reply,
                "admitted": admit, "reused": reused}

    a, b = (int(member[held]) for member, held in zip(openers, inventory, strict=True))
    a_heard, a_trace = activate("first_opening", a, left, 0, 0)
    b_heard, b_trace = activate("second_opening", b, right, 0, 0)
    mask = a_heard | b_heard
    common = {"public_opening_mask": mask, "opening_calls": [x for x in (a_trace, b_trace) if x is not None]}
    for arm in ARMS:
        query_map, responder = policies[arm]
        queried = int(query_map[mask])
        heard = 0 if arm == "erased" else queried
        reply = int(responder[right, b, heard])
        gain, trace = activate("second_reply", reply, right, mask, heard)
        cost = D.SEND_COST[a] + D.SEND_COST[b] + D.QUERY_COST[queried] + D.SEND_COST[reply]
        yield common | {"arm": arm, "asked": NAMES[queried], "heard": NAMES[heard],
                        "followup": trace, "final_mask": mask | gain, "cost": float(cost)}


def select():
    context = solve()
    points, label, law, learned, fixed, *_ = context
    for left, right in np.ndindex(law.shape):
        if law[left, right] <= 0:
            continue
        rows = {x["arm"]: x for x in simulate(context, (left, right), ideal)}
        learned_row = rows["learned"]
        raw = {arm: points[x["final_mask"]] for arm, x in rows.items()}
        if (learned_row["asked"] != "none" and raw["learned"] > raw["no_request"]
                and raw["learned"] > raw["erased"]):
            return context, (left, right), {"prior": label, "selected_team": learned, "fixed": fixed,
                   "inventories": [left, right], "modeled_joint_mass": float(law[left, right]),
                   "ideal": {name: {"mask": x["final_mask"], "score": float(raw[name]), "ask": x["asked"]}
                             for name, x in rows.items()}}
    raise ValueError("No selected mechanistic witness found")


def pins():
    inputs = (Path(__file__), HERE / "protocol.md", HERE / "plan.json", CASE_PATH, BANK_PATH,
              HERE.parents[1] / "fit.json", HERE.parent / "sparse-results.json",
              HERE.parent / "qualify.py", selector.cases.FILES["unifil"])
    return {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in inputs}


def collect(generate, directory):
    context, pair, plan = select()
    assert plan == e.read(HERE / "plan.json")

    def logged(req):
        result = generate(req)
        h.r.w.archived.base.suite.append(directory / "calls.jsonl", {"request": req, "reply": result})
        return result

    for row in simulate(context, pair, logged):
        h.r.w.archived.base.suite.append(directory / "trace.jsonl", row)
    (directory / "inputs.json").write_text(json.dumps(pins(), indent=2) + "\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("plan", "run"))
    if p.parse_args().mode == "plan":
        e.emit(select()[2])
    else:
        with patch.object(h.r.w.archived.base.suite, "collect", collect), patch.object(
                h.r.w.archived.base, "roster", return_value={"unifil": None}):
            h.r.w.archived.base.run(RUN)
