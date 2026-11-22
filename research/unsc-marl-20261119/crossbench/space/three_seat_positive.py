"""Freeze simulated compromise grids with a provable benefit from peer visibility."""
import json
from itertools import permutations, product
from pathlib import Path
import random
from unittest.mock import patch

import numpy as np
import three_seat_transfer as shared

HERE = Path(__file__).resolve().parent
SEED = 20261120
DRAW_COUNT = 160
MUTATION_DRAWS = 256
MIN_GAIN = .025
EXPECTED = 8
PACKAGES = ("A", "B", "C")
DECK = tuple(card for card in product(range(4), repeat=3) if any(card))
OPENINGS = np.array(list(product(range(6), repeat=3)))
RECEIPTS = (None, *product(range(3), range(4)))


def solve(grid, enabled):
    # Optimize all deterministic first policies, then all second local decisions.
    policy_index = OPENINGS if enabled else OPENINGS[(OPENINGS % 2 == 0).all(axis=1)]
    scores = np.zeros((3, 6, 3, len(RECEIPTS), 3))
    fees = np.zeros((3, 6))
    for world, p in grid.prior(True).items():
        for i, (col, send) in enumerate(shared.base.ACTIONS):
            first = grid.claim(world, 0, col)
            for seen, seen_p in shared.base.observations(first, send):
                j = RECEIPTS.index(seen)
                for pos in range(3):
                    second = grid.claim(world, 1, pos)
                    value = 0.
                    for got_a, got_b in product((False, True), repeat=2):
                        view = (first if got_a else None, second if got_b else None)
                        mass = (shared.base.DELIVER if got_a else 1 - shared.base.DELIVER) * (
                            shared.base.DELIVER if got_b else 1 - shared.base.DELIVER)
                        value += mass * bool(grid.information(view)[1])
                    scores[world[0], i, world[1], j, pos] += p * seen_p * value
            fees[world[0], i] += p * shared.base.FEE * send
    locally_weighted = scores[np.arange(3), policy_index].sum(axis=1)
    costs = fees[np.arange(3), policy_index].sum(axis=1)
    team_scores = locally_weighted.max(axis=-1).sum(axis=(1, 2)) - costs
    best = int(team_scores.argmax())
    first = policy_index[best]
    second = locally_weighted[best].argmax(axis=-1)
    return {"net": float(team_scores[best]), "first_actions": first.tolist(),
            "second_actions": second.tolist(), "first_rules_examined": len(policy_index)}


def fit_grids():
    rng = random.Random(SEED)
    accepted = []
    counts = {origin: {"examined": 0, "rejected_class_balance": 0} for origin in ("unstructured", "mutated_space")}
    structures = set()
    topologies = set()
    unstructured = 0
    for draw in range(DRAW_COUNT + MUTATION_DRAWS):
        origin = "unstructured" if draw < DRAW_COUNT else "mutated_space"
        if origin == "unstructured":
            cards_a, cards_b = (tuple(sorted(rng.sample(DECK, 3))) for _ in range(2))
            public = tuple(rng.randint(1, 3) for _ in PACKAGES)
        else:
            pool = [list(card) for card in (*shared.base.CARDS_A, *shared.base.CARDS_B, shared.base.PUBLIC)]
            for i in rng.sample(range(21), 3):
                seat, slot = divmod(i, 3)
                pool[seat][slot] = rng.choice([value for value in range(int(seat == 6), 4)
                                               if value != pool[seat][slot]])
            cards_a = tuple(sorted(map(tuple, pool[:3])))
            cards_b = tuple(sorted(map(tuple, pool[3:6])))
            public = tuple(pool[6])
            if any(not any(row) for row in (*cards_a, *cards_b)) or len(set(cards_a)) != 3 or len(set(cards_b)) != 3:
                continue
        identity = min(
            (tuple(public[i] for i in permutation),
             tuple(sorted(tuple(row[i] for i in permutation) for row in cards_a)),
             tuple(sorted(tuple(row[i] for i in permutation) for row in cards_b)))
            for permutation in permutations(range(3)))
        if identity in structures:
            continue
        structures.add(identity)
        with patch.dict(shared.FIXTURES, {"candidate": (PACKAGES, cards_a, cards_b, public)}):
            grid = shared.Grid("candidate")
            impasses = sum("impasse" in grid.winners(world) for world in grid.worlds)
            if impasses not in range(2, 8):
                counts[origin]["rejected_class_balance"] += 1
                continue
            counts[origin]["examined"] += 1
            peer, independent = solve(grid, True), solve(grid, False)
            gain = peer["net"] - independent["net"]
            assert gain >= -1e-12
            if gain >= MIN_GAIN:
                unstructured += int(origin == "unstructured")
                topology = tuple(sorted((len(grid.winners(world)), "impasse" in grid.winners(world),
                                         sum(bool(grid.information((grid.claim(world, 0, i),
                                                                     grid.claim(world, 1, j)))[1])
                                             for i, j in product(range(3), repeat=2)))
                                        for world in grid.worlds))
                if topology in topologies:
                    continue
                topologies.add(topology)
                accepted.append({"draw": draw, "origin": origin, "certificate_count_signature": topology,
                                 "impasses": impasses, "packages": PACKAGES, "cards_a": cards_a,
                                 "cards_b": cards_b, "public": public, "independent": independent, "peer": peer,
                                 "certified_peer_headroom": gain})
    return {"scope": "Fictional balanced grade worlds selected solely by the exact script gap. "
                     "One grade per seat, lossy chair delivery, optional paid peer signal, no chair follow-up.",
            "seed": SEED, "unstructured_draws": DRAW_COUNT, "mutated_draws": MUTATION_DRAWS,
            "unstructured_above_threshold": unstructured, "minimum_peer_advantage": MIN_GAIN,
            "screening": counts, "accepted": accepted,
            "partition": {"fit": [r["draw"] for r in accepted[:EXPECTED // 2]],
                          "reserved": [r["draw"] for r in accepted[EXPECTED // 2:EXPECTED]]}}


if __name__ == "__main__":
    print(json.dumps(fit_grids(), indent=2))
