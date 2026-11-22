"""Fit with unproductive source cards, then replay unchanged historical score banks."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

import replay as held

e, j, o = held.e, held.training, held.o
HERE = Path(__file__).resolve().parent


def discard(values, useful):
    return tuple(values[mask & useful] for mask in range(8))


def new_banks(legacy):
    originals = [tuple(row) for row in legacy["train_banks"]]
    holdout = {tuple(row) for row in legacy["holdout_banks"]}
    historical = {tuple(map(int, values - values[0])) for values in held.banks().values()}
    historical.update(tuple(map(int, pts - pts[0])) for _, _, pts, *_ in o.historical())
    rng = np.random.default_rng(j.SEED + 1)
    dense = [v for v in originals if v not in historical]
    assert len(dense) >= 72
    sources = list(j.draw_banks(rng, 500))
    candidates = tuple(dense[72:] + sources)
    train = dense[:72]
    test = set()
    for active in (2, 1):
        masks = [i for i in range(1, 8) if i.bit_count() == active]
        sampled = []
        for vals in candidates:
            meaningful = int(rng.choice(masks))
            bank = discard(vals, meaningful)
            if bank in train or bank in sampled or bank in holdout or bank in historical or bank in test:
                continue
            sampled.append(bank)
            if len(sampled) == 48:
                break
        assert len(sampled) == 48
        train += sampled[:36]
        test.update(sampled[36:])
    assert len(train) == len(set(train)) == 144
    assert not set(train) & (test | holdout | historical)
    return train, sorted(test)


def compare(bank, parameters, law, original):
    estimate = held.singleton(bank)
    openers = o.replan.study.opening(estimate, law, original)
    mass = o.opening(*openers, law)
    rows = o.controls(bank, mass, law, openers)
    for name, fit in parameters.items():
        for label, pruned in (("direct", False), ("pruned", True)):
            pair = held.learned_maps(estimate, mass, fit, law, openers, pruned)
            rows[f"{name}_{label}"] = o.measure(bank, mass, law, openers, pair)
    return rows


def run():
    original_artifact = HERE.parent / "fit.json"
    legacy = e.read(original_artifact)
    original = e.read(o.replan.study.OLD)["training"]["budget_fit"]
    training, sparse_test = new_banks(legacy)
    fit, trace = j.learn(training, original)
    parameters = {"dense_fit": [np.array(row) for row in legacy["parameters"]], "sparse_fit": fit}
    historical = {}
    replay = e.read(HERE / "results.json")["dockets"]
    for name, bank in held.banks().items():
        models = {}
        for law_id, law in j.R.TEST_PRIORS.items():
            row = compare(bank, parameters, law, original)
            baseline = replay[name]["conditions"][law_id]["singletons_pruned"]
            assert abs(row["dense_fit_pruned"]["net"] - baseline["net"]) <= 1e-10
            models[law_id] = row
        historical[name] = models
    synthetic = {}
    for name, items in (("dense", legacy["holdout_banks"]), ("sparse", sparse_test)):
        rows = {}
        for (i, values), (prior_name, law) in product(enumerate(items), j.R.TEST_PRIORS.items()):
            values = np.array(values, dtype=float)
            scored = compare(values, parameters, law, original)
            rows[f"{i}/{prior_name}"] = {"bank": values.tolist(), "net": {k: v["net"] for k, v in scored.items()}}
        synthetic[name] = rows
    pins = (Path(__file__), HERE / "sparse-protocol.md", HERE / "replay.py", HERE / "results.json",
            original_artifact, Path(j.__file__), Path(o.__file__))
    return {"training": training, "trace": trace, "parameters": [x.tolist() for x in fit],
            "historical": historical, "synthetic_holdout": synthetic,
            "sha256": {str(p.relative_to(HERE.parent)): sha256(p.read_bytes()).hexdigest() for p in pins}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
