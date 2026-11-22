"""Compare single-entry and coordinated reward-only policy search."""
import json

import numpy as np

from source_route_signal import CAPS, SIGNAL_COST, optimize, terminal_matrix

SEED = 36221
UPDATES = 240
PROPOSALS = 96
TRAINING_WEIGHTS = ((5, 8, 5), (8, 5, 6), (5, 5, 8))
TEST_WEIGHTS = (7, 7, 7)
PRIVATE = np.array(CAPS)
TYPES = np.arange(4)
SEATS = np.arange(2)
# Column zero is the announcement. The other columns are evidence choices
# indexed by the two observed bits, with the agent's own bit first.
LEGAL = np.array([[True, bool(t & 1), bool(t & 2)] for t in TYPES])


def random_tables(rng):
    tables = np.empty((PROPOSALS, 2, 4, 5), dtype=np.int8)
    tables[..., 0] = rng.integers(0, 2, size=tables.shape[:-1]) * (TYPES >= 2)
    draw = rng.random((*tables.shape[:-1], 4, 3))
    tables[..., 1:] = np.where(LEGAL[:, None], draw, -1).argmax(axis=-1)
    return tables


def play(tables, payoff):
    counts = np.arange(len(tables))[:, None, None]
    bits = tables[counts, SEATS, PRIVATE, 0]
    channels = 1 + 2 * bits + bits[..., ::-1]
    actions = tables[counts, SEATS, PRIVATE, channels]
    returns = payoff[actions[..., 0], actions[..., 1]] - SIGNAL_COST * bits.sum(axis=-1)
    return bits, actions, returns


def fit(public, coordinated, training_weights=TRAINING_WEIGHTS):
    rng = np.random.default_rng(SEED + public)
    payoff = np.mean([terminal_matrix(public, w) for w in training_weights], axis=0)
    table = np.zeros((2, 4, 5), dtype=np.int8)
    trace = []
    incumbent = float(play(table[None], payoff)[2].mean())
    for update in range(UPDATES):
        replacements = random_tables(rng)
        slots = rng.random(replacements.shape)
        one_slot = slots.reshape(PROPOSALS, -1).argmin(axis=-1)
        mutations = np.arange(table.size) == one_slot[:, None]
        mutations = mutations.reshape(replacements.shape)
        if coordinated:
            # Replace random groups of entries across the two agent policies.
            # The proposal distribution has no knowledge of the payoff table.
            mutations[PROPOSALS // 2:] = slots[PROPOSALS // 2:] < .20
        candidates = np.where(mutations, replacements, table)
        values = play(candidates, payoff)[2].mean(axis=-1)
        best = values.max()
        if best >= incumbent - 1e-10:
            choice = int(rng.choice(np.flatnonzero(np.isclose(values, best, rtol=0, atol=1e-10))))
            table = candidates[choice]
            if best > incumbent + 1e-10:
                trace.append({"update": update + 1, "return": float(best),
                              "changed_entries": int(np.count_nonzero(mutations[choice]))})
            incumbent = max(incumbent, float(best))
    return table, trace


def run():
    results = []
    for public in range(16):
        no_signal, _, optimal = optimize(public, TEST_WEIGHTS)
        row = {"public": public, "no_signal_optimal": no_signal, "optional_optimal": optimal}
        for variant in ("single_entry", "coordinated"):
            table, trace = fit(public, variant == "coordinated")
            bits, actions, returns = (x[0] for x in play(table[None], terminal_matrix(public, TEST_WEIGHTS)))
            assert np.all(bits <= ((PRIVATE & 2) != 0))
            assert np.all(LEGAL[PRIVATE, actions])
            assert returns.mean() <= optimal + 1e-9
            row[variant] = {"return": float(returns.mean()), "signals": int(bits.sum()),
                            "table": table.tolist(), "improvements": trace,
                            "worlds": [{"private": p, "signals": b.tolist(), "evidence": a.tolist(),
                                        "return": float(r)} for p, b, a, r in zip(CAPS, bits, actions, returns, strict=True)]}
        results.append(row)
    return {"seed": SEED, "updates_per_public_mask": UPDATES, "proposals_per_update": PROPOSALS,
            "training_weights": TRAINING_WEIGHTS, "test_weights": TEST_WEIGHTS, "masks": results}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
