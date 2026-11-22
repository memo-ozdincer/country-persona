"""Qualify learned historical continuations using only four score observations."""
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

import replay as cases

o, e = cases.o, cases.e
HERE = Path(__file__).resolve().parent


def choose(coords, openers, law, params):
    base, *increments = coords
    masks = (np.arange(8)[:, None] & np.array([1, 2, 4])) != 0
    estimate = np.minimum(70, base + masks @ (np.array(increments) - base))
    mass = o.opening(*openers, law)
    quiet = o.exact_parts(mass, estimate)["exact_no_request"]
    options = {"dense": cases.learned_maps(estimate, mass, params[0], law, openers, True),
               "sparse": cases.learned_maps(estimate, mass, params[1], law, openers, True), "quiet": quiet}
    for card in range(1, 4):
        q = np.where(o.D.CHAIR_LEGAL[:, card], card, 0)
        options[f"fixed_{card}"] = (q, o.choose_response(q, mass, estimate))
    predicted = {name: o.measure(estimate, mass, law, openers, action) for name, action in options.items()}
    learned = max(("dense", "sparse", "quiet"), key=lambda x: (predicted[x]["net"], x == "quiet"))
    all_arms = max(options, key=lambda x: (predicted[x]["net"], x == "quiet"))
    return {"learned_and_quiet": learned, "including_fixed": all_arms}, options, predicted, mass


def replay_case(bank, law, params, original):
    coords = tuple(float(bank[i]) for i in (0, 1, 2, 4))
    estimated = cases.singleton(bank)
    openers = o.replan.study.opening(estimated, law, original)
    picked, options, forecast, mass = choose(coords, openers, law, params)
    observed = {k: o.measure(bank, mass, law, openers, pair) for k, pair in options.items()}
    comparisons = o.controls(bank, mass, law, openers)
    exact = comparisons["exact_ask_reply"]["net"]
    assert all(row["net"] <= exact + 1e-10 for row in observed.values())
    result = {}
    for variant, option in picked.items():
        expected, actual = forecast[option], observed[option]
        result[variant] = {"policy": option, "forecast_net": expected["net"], "actual": actual,
                          "gain_over_exact_no_request": actual["net"] - comparisons["exact_no_request"]["net"],
                          "released_gain_over_exact_no_request": actual["released"] - comparisons["exact_no_request"]["released"]}
    return result | {"collected_scores": coords, "observed": observed,
                     "best_fixed_actual": max(comparisons[f"fixed_{i}_exact_reply"]["net"] for i in range(1, 4)),
                     "exact_no_request": comparisons["exact_no_request"], "exact_adaptive": comparisons["exact_ask_reply"]}


def run():
    former, few = HERE.parent / "fit.json", HERE / "sparse-results.json"
    params = tuple([np.array(a) for a in e.read(path)["parameters"]] for path in (former, few))
    original = e.read(o.replan.study.OLD)["training"]["budget_fit"]
    result = {name: {tag: replay_case(bank, law, params, original) for tag, law in o.R.TEST_PRIORS.items()}
              for name, bank in cases.banks().items()}
    pins = (Path(__file__), HERE / "selector-protocol.md", HERE / "replay.py", former, few, *cases.FILES.values())
    return {"archive_cases": result, "sha256": {str(p.relative_to(o.h.ARCHIVE.parents[2])): sha256(p.read_bytes()).hexdigest()
                                               for p in pins}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
