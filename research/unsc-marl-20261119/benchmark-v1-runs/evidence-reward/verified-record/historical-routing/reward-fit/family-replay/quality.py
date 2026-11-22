"""Replay a documentary quality floor before optimizing net."""
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

import qualify as selector

HERE = Path(__file__).resolve().parent
tests, o, e = selector.cases, selector.o, selector.e


def run():
    former, sparse = HERE.parent / "fit.json", HERE / "sparse-results.json"
    params = tuple([np.array(a) for a in e.read(p)["parameters"]] for p in (former, sparse))
    original = e.read(o.replan.study.OLD)["training"]["budget_fit"]
    saved = e.read(HERE / "qualified-results.json")["archive_cases"]
    result = {}
    for name, scores in tests.banks().items():
        rows = {}
        for tag, law in o.R.TEST_PRIORS.items():
            projected = tests.singleton(scores)
            openers = o.replan.study.opening(projected, law, original)
            coords = tuple(float(scores[i]) for i in (0, 1, 2, 4))
            previous, options, forecast, mass = selector.choose(coords, openers, law, params)
            floor = forecast["quiet"]["released"]
            allowed = [arm for arm in options if forecast[arm]["released"] >= floor - 1e-10]
            picked = max(allowed, key=lambda arm: (forecast[arm]["net"], arm == "quiet"))
            actual = o.measure(scores, mass, law, openers, options[picked])
            archived = saved[name][tag]
            assert archived["including_fixed"]["policy"] == previous["including_fixed"]
            assert archived["observed"][picked] == actual
            quiet = archived["exact_no_request"]
            rows[tag] = {"policy": picked, "forecast": forecast[picked]["released"], "forecast_floor": floor,
                         "admissible_candidates": allowed, "actual": actual,
                         "net_gain": actual["net"] - quiet["net"], "released_gain": actual["released"] - quiet["released"]}
        result[name] = rows
    pins = (Path(__file__), HERE / "quality-protocol.md", HERE / "qualify.py", HERE / "qualified-results.json")
    return {"conditions": result, "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in pins}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
