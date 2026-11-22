"""Check the effects of native margins and fitted weights separately, after scoring."""
from itertools import product
from pathlib import Path
from statistics import mean

import numpy as np

import held_native as held
import reward_head as head

HERE, READ = head.HERE, head.READ


def trial(world, weights):
    fit = {"heads": {name: [{"weights": weights}] for name in ("hybrid", "typed_only")}}
    result = head.score(world, fit)
    return {"with_native": result["hybrid"], "without_native": result["typed_only"]}


def run():
    fit = READ(HERE / "fit.json")
    scores = READ(HERE / "scores.json")
    outputs = READ(HERE / "verified.json")["outputs"]
    _, _, raw, edges, true = held.setup()
    local = [np.asarray(values) for values in raw]
    weights = {name: trace[-1]["weights"] for name, trace in fit["heads"].items()}
    weights["fixed_refreshed"] = [1., 0., 1.]
    rows = {}
    for share, rate in product(held.SHARES, held.RATES):
        key = f"{share}/{rate}"
        modes = head.sample(local, edges, rate, share, true, outputs, key)
        rows[key] = {mode: {name: trial(world, w) for name, w in weights.items()}
                     for mode, world in modes.items()}
        for mode, values in rows[key].items():
            for expected, name, setting in (("hybrid", "hybrid", "with_native"),
                                            ("typed_only", "typed_only", "without_native"),
                                            ("fixed_refreshed", "fixed_refreshed", "without_native")):
                assert values[name][setting] == scores["held"][key][mode][expected]
    means = {
        mode: {
            name: {
                setting: mean(row[mode][name][setting]["released"] for row in rows.values())
                for setting in ("with_native", "without_native")
            }
            for name in weights
        }
        for mode in head.MODES
    }
    pins = (Path(__file__), HERE / "scores.json", HERE / "fit.json", HERE / "verified.json")
    return {"post_hoc": True, "weights": weights, "means": means, "rows": rows,
            "sources": {str(path.relative_to(head.RUNS)): head.prior.digest(path) for path in pins}}


if __name__ == "__main__":
    head.native.frozen.emit(run())
