"""Lock prefix feasibility and frozen-policy routing on Resolution 2466."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
KIT = HERE.parent
sys.path.insert(0, str(KIT))
import facilitator_budget_policy as budget

D, fit, joint, R = budget.D, budget.fit, budget.joint, budget.R
PACKET = HERE / "packet.json"
FIT = budget.EVIDENCE / "results.json"
FORECAST = HERE / "forecast.json"


def read(path):
    return json.loads(path.read_text())


def bank(packet, cap, whole):
    atoms = [(i, row) for i, card in enumerate(packet["cards"]) for row in card["atoms"]]
    best, costs = [packet["base_points"]] * 8, [0] * 8
    for received in range(8):
        feasible = []
        for mask in range(1 << len(atoms)):
            eligible = [mask >> i & 1 for i in range(len(atoms))]
            assert len(eligible) == 6
            if whole and any(eligible[i] != eligible[i + 1] for i in range(0, 6, 2)):
                continue
            pieces = [pair for keep, pair in zip(eligible, atoms, strict=True) if keep]
            desks = {slot for slot, _ in pieces}
            if any(not (received & (1 << s)) for s in desks):
                continue
            size = (sum(len(row["text"].split()) for _, row in pieces)
                    + sum(len(packet["cards"][s]["desk"].split()) for s in desks))
            if size > cap:
                continue
            earned = sum(row["points"] for _, row in pieces)
            if set(packet["joint"]["needs"]) <= {row["id"] for _, row in pieces}:
                earned += packet["joint"]["points"]
            feasible.append((packet["base_points"] + earned, -size))
        best[received], cost = max(feasible)
        costs[received] = -cost
    return np.asarray(best), costs


def run():
    pkt = read(PACKET)
    model = read(FIT)["training"]["budget_fit"]
    prior = R.TEST_PRIORS["uniform"]
    curves = {}
    for cap in pkt["limits"]:
        prefix, costs = bank(pkt, cap, whole=False)
        whole, _ = bank(pkt, cap, whole=True)
        curves[str(cap)] = {"prefix": prefix.tolist(), "minimum_prefix_words": costs, "whole": whole.tolist()}
    target = np.asarray(curves["70"]["prefix"])
    whole = np.asarray(curves["70"]["whole"])
    team, _ = budget.adaptive.contextual_policies(target, prior, model)
    left, right, learned_q, learned_r = team
    mass = joint.opening(left, right, prior)
    exact_q, exact_r = fit.exact(target, mass, fit.PERFECT)
    whole_q, whole_r = fit.exact(whole, mass, fit.PERFECT)
    candidates = []
    for l, r in product(range(1, 8), repeat=2):
        a, b = int(left[l]), int(right[r])
        if not a or not b or a == b:
            continue
        opening = (1 << (a - 1)) | (1 << (b - 1))
        missing, = set(range(1, 4)) - {a, b}
        if not r & (1 << (missing - 1)):
            continue
        q = int(learned_q[opening])
        candidate = {"inventories": [l, r], "openings": [a, b], "receipt": opening, "missing": missing}
        tail = {"learned": [q, int(learned_r[r, b, q])],
                "silence": [0, int(learned_r[r, b, 0])],
                "prefix_planning": [int(exact_q[opening]), int(exact_r[r, b, exact_q[opening]])],
                "whole_planning": [int(whole_q[opening]), int(whole_r[r, b, whole_q[opening]])],
                "fixed_missing": [0, missing]}
        assert all(c == 0 or r & (1 << (c - 1)) for _, c in tail.values())
        candidate["tail"] = tail
        receive = lambda c: opening | ((1 << (c - 1)) if c else 0)
        candidate["benefit_by_arm"] = {k: int(target[receive(c)] - target[opening]) for k, (_, c) in tail.items()}
        candidates.append(candidate)
    # Select from frozen action forecasts, before generating any model text.
    ordered = sorted(candidates, key=lambda c: (c["inventories"], c["receipt"]))
    gain = lambda c: c["benefit_by_arm"]["learned"] - c["benefit_by_arm"]["silence"]
    responsive = max(ordered, key=gain)
    control = min(ordered, key=gain)
    assert responsive != control
    quiet = (left, right, *fit.exact(target, mass, fit.PERFECT, independent=True))
    teams = {"learned": team, "prefix_planning": (left, right, exact_q, exact_r),
             "whole_planning": (left, right, whole_q, whole_r), "exact_no_request": quiet}
    scores = {name: joint.metric(roles, prior, target, fit.PERFECT) for name, roles in teams.items()}
    return {"event": pkt["event"], "curves": curves, "aggregate_uniform_modeled": scores,
            "candidate_worlds": len(ordered), "worlds": {"opportunity": responsive, "control": control},
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in (PACKET, FIT, HERE / "protocol.md")}}


if __name__ == "__main__":
    print(json.dumps(run(),ensure_ascii=False,indent=2))
