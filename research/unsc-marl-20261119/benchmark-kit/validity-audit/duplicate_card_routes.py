"""Learn evidence routing when either desk can supply the same source card."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import sys

import numpy as np

from source_route_fit import MESSAGE_COST
from source_route_search import LEGAL, PRIVATE, PROPOSALS, SEED, UPDATES, play, random_tables
from source_route_signal import ANNOUNCEMENTS, PHASES, POLICIES, SIGNAL_COST

CASE = Path(__file__).with_name("source-record-venezuela-routing.json")
TEST = {
    "all_inventories": np.ones(len(PRIVATE)) / len(PRIVATE),
    "nonempty_desks": np.all(PRIVATE != 0, axis=1) / 9,
}
TRAIN_MARGINALS = ((.12, .27, .27, .34), (.22, .18, .18, .42))
TRAIN = np.mean([np.outer(p, p).flatten() for p in TRAIN_MARGINALS], axis=0)
POINTS = 7
CARDS = np.arange(3)
PROOF = np.array([[len({i, j} - {0}) for j in CARDS] for i in CARDS])
PRESENT = (CARDS != 0).astype(int)
PAYOFF = POINTS * PROOF - MESSAGE_COST * (PRESENT[None, :] + PRESENT[:, None])
LEARNED_VARIANT = {"training_marginals": TRAIN_MARGINALS, "updates": UPDATES,
                   "proposals_per_update": PROPOSALS, "seed": SEED}


def exact(prior, matrix, signal_cost):
    left, right = [POLICIES[:, PRIVATE[:, s]] for s in (0, 1)]
    values = matrix[left[:, None], right[None, :]]
    results = {}
    best = (-np.inf, None, None)
    for first, second in product(ANNOUNCEMENTS, repeat=2):
        bits = np.asarray([first, second])[np.arange(2), PRIVATE]
        actions = np.zeros_like(PRIVATE)
        for phase in PHASES:
            view = np.all(bits == phase, axis=1)
            scores = (values * (prior * view)).sum(axis=-1)
            a, b = np.unravel_index(scores.argmax(), scores.shape)
            actions[view] = np.stack((left[a, view], right[b, view]), axis=1)
        net = float(prior @ (matrix[actions[:, 0], actions[:, 1]] - signal_cost * bits.sum(axis=1)))
        if net > best[0] + 1e-10:
            best = (net, bits, actions)
        if first == second == ANNOUNCEMENTS[0]:
            results["silent"] = (net, bits, actions)
        if first == second == ANNOUNCEMENTS[-1]:
            results["always"] = (net, bits, actions)
    results["optional"] = best
    return results


def fit():
    rng = np.random.default_rng(SEED)
    table = np.zeros((2, 4, 5), dtype=np.int8)
    incumbent = float(play(table[None], PAYOFF)[2][0] @ TRAIN)
    trace = []
    for step in range(UPDATES):
        replacements = random_tables(rng)
        draws = rng.random(replacements.shape)
        one_slot = draws.reshape(PROPOSALS, -1).argmin(axis=1)
        edit = (np.arange(table.size) == one_slot[:, None]).reshape(replacements.shape)
        edit[PROPOSALS // 2:] = draws[PROPOSALS // 2:] < .2
        candidates = np.where(edit, replacements, table)
        values = play(candidates, PAYOFF)[2] @ TRAIN
        best = values.max()
        if best >= incumbent - 1e-10:
            choice = rng.choice(np.flatnonzero(np.isclose(values, best, rtol=0, atol=1e-10)))
            table = candidates[choice]
            if best > incumbent + 1e-10:
                trace.append({"update": step + 1, "training_return": float(best)})
            incumbent = max(incumbent, float(best))
    return table, trace


def summarize(prior, bits, actions):
    assert np.all(bits <= ((PRIVATE & 2) != 0)) and np.all(LEGAL[PRIVATE, actions])
    left, right = actions.T
    proof_points = POINTS * PROOF[left, right]
    return {
        "net": float(prior @ (PAYOFF[left, right] - SIGNAL_COST * bits.sum(axis=1))),
        "proof_points": float(prior @ proof_points),
        "authored_reference_points": 56 + float(prior @ proof_points),
        "worlds": [{"inventories": private.tolist(), "signals": signal.tolist(),
                    "actions": action.tolist(), "probability": float(probability)}
                   for private, signal, action, probability in zip(PRIVATE, bits, actions, prior, strict=True)],
    }


def run(train):
    report = {"case_sha256": sha256(CASE.read_bytes()).hexdigest(), "training": LEARNED_VARIANT, "arms": {}}
    if train:
        table, history = fit()
        bits, actions, _ = [out[0] for out in play(table[None], PAYOFF)]
        report["learned_table"] = table.tolist()
        report["improvements"] = history
    for name, prior in TEST.items():
        raw = exact(prior, POINTS * PROOF, 0)
        net = exact(prior, PAYOFF, SIGNAL_COST)
        rows = {arm: {**summarize(prior, signal, delivery), "coverage_ceiling": raw[arm][0]}
                for arm, (_, signal, delivery) in net.items()}
        if train:
            rows["learned"] = summarize(prior, bits, actions)
            assert rows["learned"]["net"] <= rows["optional"]["net"] + 1e-9
            assert rows["learned"]["proof_points"] <= rows["optional"]["coverage_ceiling"] + 1e-9
        report["arms"][name] = rows
    return report


if __name__ == "__main__":
    if sys.argv[1:] not in ([], ["--fit"]):
        raise SystemExit("usage: duplicate_card_routes.py [--fit]")
    print(json.dumps(run(bool(sys.argv[1:])), indent=2))
