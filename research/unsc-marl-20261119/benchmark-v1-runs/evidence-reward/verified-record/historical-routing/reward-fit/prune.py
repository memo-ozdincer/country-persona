"""Reduce contact while preserving the learned reply policy and its actual inputs."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

import joint_fit as j

o, e = j.o, j.e
HERE = Path(__file__).resolve().parent


def improve(points, law, openers, mass, params, refresh):
    q, initial_reply = j.paired(points, mass, params)
    energy = o.measure(points, mass, law, openers, (q, initial_reply))
    original = energy
    removed = []
    visits = mass.sum((0, 1))
    while True:
        candidates = []
        for state in np.flatnonzero((q != 0) & (visits > 1e-12)):
            proposed = q.copy()
            proposed[state] = 0
            reply = j.paired_quiet(points, mass, params, proposed) if refresh else initial_reply
            result = o.measure(points, mass, law, openers, (proposed, reply))
            if result["net"] > energy["net"] + 1e-10:
                candidates.append((result["net"], int(state), proposed, result))
        if not candidates:
            break
        _, state, q, energy = max(candidates, key=lambda row: (row[0], -row[1]))
        removed.append(state)
    reply = j.paired_quiet(points, mass, params, q) if refresh else initial_reply
    reevaluated = o.measure(points, mass, law, openers, (q, reply))
    assert abs(reevaluated["net"] - energy["net"]) <= 1e-10
    return {"net": energy["net"], "queries": energy["queries"],
            "gain": energy["net"] - original["net"], "removed_states": removed}


def compare(points, law, openers, mass, params, earlier):
    result = {mode: improve(points, law, openers, mass, params, refresh)
              for mode, refresh in (("refreshed_reply", True), ("unchanged_reply", False))}
    assert all(earlier["joint_fit"] <= row["net"] + 1e-10 <= earlier["exact_ask_reply"] + 2e-10
               for row in result.values())
    return result | {"unpruned": earlier["joint_fit"], "exact_no_request": earlier["exact_no_request"],
                     "exact": earlier["exact_ask_reply"], "best_fixed": max(earlier[f"fixed_{k}_exact_reply"] for k in (1, 2, 3))}


def run():
    source = e.read(HERE / "fit.json")
    params = [np.array(weights) for weights in source["parameters"]]
    historical = {}
    for endpoint, label, points, law, openers, mass, _ in o.historical():
        earlier = {key: scored["net"] for key, scored in source["historical"][endpoint][label]["rows"].items()}
        historical.setdefault(endpoint, {})[label] = compare(points, law, openers, mass, params, earlier)
    synthetic = {}
    study = o.replan.study
    original = e.read(study.OLD)["training"]["budget_fit"]
    for i, (values, label) in enumerate(product(source["holdout_banks"], j.R.TEST_PRIORS)):
        earlier = source["synthetic_holdout"][str(i)]
        assert values == earlier["bank"] and label == earlier["law"]
        law, points = j.R.TEST_PRIORS[label], np.array(values, dtype=float)
        openers = study.opening(points, law, original)
        synthetic[str(i)] = compare(points, law, openers, o.opening(*openers, law), params, earlier["net"])
    pins = (Path(__file__), HERE / "prune-protocol.md", HERE / "fit.json", Path(j.__file__), Path(o.__file__))
    return {"historical": historical, "synthetic": synthetic,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in pins}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
