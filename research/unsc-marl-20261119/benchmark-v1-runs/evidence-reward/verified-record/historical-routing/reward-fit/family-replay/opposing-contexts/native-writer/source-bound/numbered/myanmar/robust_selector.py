"""Choose a routing policy against uncertain pair calibration."""
from hashlib import sha256
from pathlib import Path

import numpy as np

import evaluate_transfer as q

t, m, n = q.t, q.m, q.n
PAIR = 3
TOLERANCE = 1e-10


def forecasts(singletons, reviewed):
    masks = np.arange(8)
    forecast = []
    for shift in (-7, 0, 7):
        result = singletons.copy()
        pair_grade = float(np.clip(reviewed + shift, 0, 70))
        has_pair = masks & PAIR == PAIR
        result[has_pair] = np.clip(result[has_pair] + pair_grade - result[PAIR], 0, 70)
        assert result[PAIR] == pair_grade
        forecast.append(result)
    return forecast


def catalog(curve, mass, prior, openings, parameters):
    silence = np.zeros(mass.shape[-1], dtype=int)
    script = {"quiet": (silence, m.o.choose_response(silence, mass, curve))}
    for card in range(1, 4):
        qmap = np.where(m.D.CHAIR_LEGAL[:, card], card, 0)
        script[f"fixed_{card}"] = (qmap, m.o.choose_response(qmap, mass, curve))
    learned = {tag: m.data.learned_maps(curve, mass, fit, prior, openings, with_pruning=True)
               for tag, fit in zip(("dense", "sparse"), parameters, strict=True)}
    return script, learned


def decide(singletons, reviewed, mass, prior, openings, parameters):
    views = forecasts(singletons, reviewed)
    menus = [catalog(curve, mass, prior, openings, parameters) for curve in views]
    candidates = {(i, kind): policy for i, (script, fit) in enumerate(menus)
                  for kind, policy in (script | fit).items()}

    def measure(curve, policy):
        return m.o.measure(curve, mass, prior, openings, policy)

    comparators = []
    for curve, (script, _) in zip(views, menus, strict=True):
        baseline = {tag: measure(curve, policy) for tag, policy in script.items()}
        comparators.append((baseline["quiet"]["released"], max(r["net"] for r in baseline.values())))
    values = {}
    for name, policy in candidates.items():
        forecasts_by_policy = [measure(c, policy) for c in views]
        documentation = min(row["released"] - silence for row, (silence, _) in zip(forecasts_by_policy, comparators))
        margin = min(row["net"] - fixed for row, (_, fixed) in zip(forecasts_by_policy, comparators))
        values[name] = (documentation, margin, forecasts_by_policy[1])
    point = [name for name, (quality, margin, center) in values.items()
             if name[0] == 1 and center["released"] >= comparators[1][0] - TOLERANCE]
    nominal = max(point, key=lambda k: (values[k][2]["net"], k[1] == "quiet"))
    robust_choices = [name for name, (quality, _, _) in values.items() if quality >= -TOLERANCE]
    if robust_choices:
        robust = max(robust_choices, key=lambda k: (values[k][1], values[k][2]["net"], k == nominal))
    else:
        robust = max(values, key=lambda k: (values[k][0], values[k][1], values[k][2]["net"]))
    return {mode: {"key": (k[0] - 1, k[1]), "policy": candidates[k],
                   "worst_forecast_quality_delta": values[k][0], "worst_forecast_net_margin": values[k][1]}
            for mode, k in (("nominal", nominal), ("robust", robust))}


def run():
    files = (t.HERE / "intact-results.json", t.HERE.parent / "packed-results.json")
    myanmar = np.array(n.read(files[0])["rank_normalized"]["bank"])
    unifil = np.array(n.read(files[1])["native"]["population"]["bank"])
    parameters = tuple([np.array(a) for a in n.read(p)["parameters"]]
                       for p in (m.HERE.parents[1] / "fit.json", m.HERE.parent / "sparse-results.json"))
    original = n.read(m.o.replan.study.OLD)["training"]["budget_fit"]
    rows = {}
    for name, bank in (("myanmar", myanmar), ("unifil", unifil)):
        singletons = t.cal.estimated(bank)
        for label, prior in m.o.R.TEST_PRIORS.items():
            openings = m.o.replan.study.opening(singletons, prior, original)
            mass = m.o.opening(*openings, prior)
            truth = m.o.controls(bank, mass, prior, openings)
            fixed = max(r["net"] for tag, r in truth.items() if tag != "exact_ask_reply")
            for shift in (-7, 0, 7):
                key = f"{name}/{label}/{shift}"
                selected = decide(singletons, bank[PAIR] + shift, mass, prior, openings, parameters)
                rows[key] = {}
                for mode, record in selected.items():
                    actions = record.pop("policy")
                    held = m.o.measure(bank, mass, prior, openings, actions)
                    assert held["net"] <= truth["exact_ask_reply"]["net"] + TOLERANCE
                    record["held_net_margin"] = held["net"] - fixed
                    record["held_quality_delta"] = held["released"] - truth["exact_no_request"]["released"]
                    rows[key][mode] = record
    pins = (Path(__file__), t.HERE / "robust-calibration.md", *files)
    return {"rows": rows, "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in pins}}


if __name__ == "__main__":
    q.e.emit(run())
