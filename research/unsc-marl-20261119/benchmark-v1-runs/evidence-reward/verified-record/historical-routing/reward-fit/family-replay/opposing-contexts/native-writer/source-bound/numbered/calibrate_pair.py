"""Check whether one two-card grade repairs the forecast for frozen routing."""
from hashlib import sha256
from pathlib import Path

import numpy as np

import numbered as w

n, m, e = w.n, w.n.matched, w.e


def estimated(bank, observed_pair=0):
    output = m.data.singleton(bank)
    if observed_pair:
        match = np.bitwise_and(np.arange(8), observed_pair) == observed_pair
        output[match] += bank[observed_pair] - output[observed_pair]
        output = np.clip(output, 0, 70)
        assert output[observed_pair] == bank[observed_pair]
    assert np.array_equal(output[[0, 1, 2, 4]], bank[[0, 1, 2, 4]])
    return output


def assess(bank, prior, parameters, original):
    singleton = estimated(bank)
    opening = m.o.replan.study.opening(singleton, prior, original)
    mass = m.o.opening(*opening, prior)
    actual = m.o.controls(bank, mass, prior, opening)
    ceiling = actual["exact_ask_reply"]["net"]
    baseline = max(x["net"] for name, x in actual.items() if name != "exact_ask_reply")
    forecasts = {}
    for pair in (0, 3, 5, 6):
        curve = estimated(bank, pair)
        candidates = m.o.exact_parts(mass, curve)
        for name, weights in zip(("dense", "sparse"), parameters):
            candidates[name] = m.data.learned_maps(curve, mass, weights, prior, opening, with_pruning=True)
        actual_rows = {policy: m.o.measure(bank, mass, prior, opening, actions)
                       for policy, actions in candidates.items()}
        assert all(row["net"] <= ceiling + 1e-10 for row in actual_rows.values())
        forecasts[pair] = {"estimate": curve.tolist(),
                           "max_error": float(np.abs(curve - bank).max()),
                           "margins_over_exact_fixed": {k: v["net"] - baseline for k, v in actual_rows.items()},
                           "released": {k: v["released"] for k, v in actual_rows.items()}}
    return {"exact_margin": ceiling - baseline, "forecasts": forecasts}


def run():
    path = w.HERE / "packed-results.json"
    banks = m.data.banks()
    native = np.array(n.read(path)["native"]["population"]["bank"], dtype=float)
    parameters = tuple([np.array(a) for a in e.read(p)["parameters"]]
                       for p in (m.HERE.parents[1] / "fit.json", m.HERE.parent / "sparse-results.json"))
    original = e.read(m.o.replan.study.OLD)["training"]["budget_fit"]
    archived = {name: {law: assess(bank, prior, parameters, original) for law, prior in m.o.R.TEST_PRIORS.items()}
                for name, bank in banks.items()}
    evaluated = {law: assess(native, prior, parameters, original) for law, prior in m.o.R.TEST_PRIORS.items()}
    pins = (Path(__file__), w.HERE / "calibration-protocol.md", path, *m.data.FILES.values())
    return {"archived": archived, "numbered_unifil": evaluated,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in pins}}


if __name__ == "__main__":
    e.emit(run())
