"""Find a clean Somalia branch where hearing the query changes the record."""
from hashlib import sha256
from itertools import product
from pathlib import Path

import numpy as np

import match as k
import delivery_runtime as dispatch

n, t, r, o, a, e, D = k.n, k.t, k.r, k.o, k.a, k.e, k.D
HERE = Path(__file__).resolve().parent


def run():
    path = t.HERE / "numeric-results.json"
    bank = np.array(n.read(path)["score_banks"]["native"])
    calibration = {i: bank[i] for i in range(7) if i != 3}
    initial = n.read(o.replan.study.OLD)["training"]["budget_fit"]
    cases = []
    for label, (law, _) in a.laws().items():
        openings = o.replan.study.opening(r.f.views(bank)["4"], law, initial)
        observed = o.opening(*openings, law)
        policy = r.evaluate_locked(calibration, bank[3], law, openings, observed, {})
        team, fixed = (policy[arm][1] for arm in ("interval_team", "interval_fixed"))
        for left, right in np.ndindex(law.shape):
            prior = law[left, right]
            if not prior:
                continue
            for first, second in product((0, 1), repeat=2):
                flow = (first, second, 1, 1)
                states = {"team": dispatch.episode((left, right), openings, team, flow),
                          "erased": dispatch.episode((left, right), openings, team, (first, second, 0, 1)),
                          "fixed": dispatch.episode((left, right), openings, fixed, flow)}
                value = {name: float(bank[state["receipt"]]) for name, state in states.items()}
                if value["team"] <= max(value["fixed"], value["erased"]):
                    continue
                weight = float(prior * D.LOSS ** (2 - first - second) * (1 - D.LOSS) ** (2 + first + second))
                cases.append({"prior": label, "world": (left, right), "delivery": flow, "routes": states,
                              "released": value, "modeled_weight": weight})
    cases.sort(key=lambda x: (-(x["released"]["team"] - x["released"]["erased"]), -x["modeled_weight"]))
    pins = (Path(__file__), path, Path(dispatch.__file__))
    return {"qualifying_branches": len(cases), "first": cases[:1],
            "sha256": {file.name: sha256(file.read_bytes()).hexdigest() for file in pins}}


if __name__ == "__main__":
    e.emit(run())
