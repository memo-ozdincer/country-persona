"""Learn only the two uncertain documentary reward entries from rollouts."""
import json
from itertools import product
from pathlib import Path
from statistics import mean

import numpy as np

import rollout_fit as s

HERE = Path(__file__).resolve().parent
MISSING = (3, 7)
STRENGTH = (0., .25, .5, 1.)
NO_FIT = [(np.zeros(7), np.zeros(6)) for _ in range(s.ROUNDS)]


def features(forecast):
    g = (forecast - forecast[0]) / 10.
    a, b, c = g[[1, 2, 4]]
    p, q, r = g[[3, 5, 6]]
    return np.array([1., a + b, abs(a - b), c, p - a - b, q - a - c,
                     r - b - c, g[7] - max(p, q, r)])


def corrected(forecast, weights, strength):
    altered = forecast.copy()
    altered[list(MISSING)] = np.clip(altered[list(MISSING)] + strength * (weights @ features(forecast)), 0, 70)
    assert np.array_equal(altered[[0, 1, 2, 4, 5, 6]], forecast[[0, 1, 2, 4, 5, 6]])
    return altered


def contexts(banks, locked, init):
    for bank, law, offset in product(banks, s.o.R.TEST_PRIORS.values(), locked["offsets"]):
        points = np.array(bank, dtype=float)
        opening, mass, forecast = s.context(points, np.clip(points[3] + offset, 0, 70), law, init)
        yield points, law, opening, mass, forecast


def fit(banks, locked, init):
    rng = np.random.default_rng(s.SEED + 1)
    feats, rewards = [], []
    visits = {mask: 0 for mask in MISSING}
    for points, law, opening, mass, forecast in contexts(banks, locked, init):
        right, own, receipt, ok = s.rolls(law, opening, rng)
        finish = receipt[:, None] | s.BITS * ok[:, 3, None]
        active = s.LEGAL[right, own, np.zeros_like(own)]
        changed = np.stack([(finish == mask).astype(float) - (receipt[:, None] == mask) for mask in MISSING], axis=-1)
        informative = active & np.any(changed != 0, axis=-1)
        for i, mask in enumerate(MISSING):
            visits[mask] += int(np.count_nonzero(active & (changed[..., i] != 0)))
        model = (changed[..., None] * features(forecast)).reshape(s.DRAWS, 4, -1)
        gain = (points[finish] - points[receipt, None]) - (forecast[finish] - forecast[receipt, None])
        feats.append(model[informative])
        rewards.append(gain[informative])
    assert all(visits.values())
    weights, trace = s.fit_ridge(feats, rewards)
    return weights.reshape(2, -1), trace, visits


def score_row(points, law, opening, mass, forecast, weights, strength):
    candidate = corrected(forecast, weights, strength)
    policy = s.deploy(candidate, mass, NO_FIT)
    return s.metric(points, law, opening, policy)


def calibrate(banks, locked, init, weights):
    trials = list(contexts(banks, locked, init))
    means = {str(scale): mean(score_row(*row, weights, scale)["net"] for row in trials) for scale in STRENGTH}
    chosen = max(STRENGTH, key=lambda scale: (means[str(scale)], -scale))
    return chosen, means, len(trials)


def run():
    locked = s.wire.n.read(HERE / "plan.json")
    assert locked == s.plan()
    previous = s.wire.n.read(HERE / "results.json")
    init = s.wire.n.read(s.INITIAL)["training"]["budget_fit"]
    training, validation = locked["training_banks"][:36], locked["training_banks"][36:]
    assert len(validation) == 12 and not {s.centered(bank) for bank in training} & {s.centered(bank) for bank in validation}
    weights, fit_trace, visits = fit(training, locked, init)
    chosen, validation_net, count = calibrate(validation, locked, init, weights)
    rows = []
    laws = s.a.laws()
    for row in previous["rows"]:
        bank = np.array(locked["test_banks"][row["case"]], dtype=float)
        law, proxy = laws[row["law"]]
        announced = law if row["information"] == "exact" else proxy
        opening, mass, forecast = s.context(bank, np.clip(bank[3] + row["review_offset"], 0, 70), announced, init)
        assert [x.tolist() for x in opening] == row["opening"]
        no_fit = score_row(bank, law, opening, mass, forecast, weights, 0.)
        assert no_fit == row["outcomes"]["no_fit"]
        scores = {name: score_row(bank, law, opening, mass, forecast, weights, scale)
                  for name, scale in (("selected", chosen), ("full", 1.))}
        for result in scores.values():
            assert result["net"] <= row["outcomes"]["informed_adaptive"]["net"] + 1e-9
        rows.append({k: row[k] for k in ("case", "law", "information", "review_offset", "silence_quality")} |
                    {"outcomes": row["outcomes"] | scores,
                     "nominal_uncertain_grades": forecast[list(MISSING)].tolist(),
                     "corrected_uncertain_grades": corrected(forecast, weights, chosen)[list(MISSING)].tolist()})
    summary = {mode: {
        **{f"vs_{reference}": s.compare([row["outcomes"][mode]["net"] - row["outcomes"][reference]["net"] for row in rows])
           for reference in ("no_fit", "fixed_forecast", "exact_forecast", "informed_fixed")},
        "below_silence": sum(row["outcomes"][mode]["released"] < row["silence_quality"] - 1e-9 for row in rows),
    } for mode in ("selected", "full", "no_fit")}
    pins = (Path(__file__), HERE / "reward-protocol.md", HERE / "plan.json", HERE / "results.json",
            HERE / "components.json", Path(s.__file__))
    return {"weights": weights.tolist(), "training_banks": len(training), "validation_banks": len(validation),
            "validation_conditions": count, "selected_strength": chosen, "validation_net": validation_net,
            "visits_on_reward_entries": visits, "fit_trace": fit_trace, "summary": summary,
            "rows": rows, "sha256": {file.name: s.digest(file) for file in pins}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
