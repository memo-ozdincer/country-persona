"""Quantify sensitivity to valid messages that omit a required qualifier."""
from hashlib import sha256
from itertools import product
from pathlib import Path

import numpy as np

import structured_live as s
import delivery_runtime as runtime

c, w = s.c, s.w
o, a, r, n = w.o, w.a, w.r, w.n
HERE = Path(__file__).resolve().parent
RATES = (0., .10, .25, .50, 1.)


def exposure(law, openings, actions, bank):
    """Compute the expected grade loss if the addressed reply is always partial."""
    price = 0.
    exposure = 0.
    for left, right in np.ndindex(law.shape):
        weight = law[left, right]
        if weight == 0:
            continue
        for first, second in product((0, 1), repeat=2):
            row = runtime.episode((left, right), openings, actions, (first, second, 1, 1))
            if row["responder_view"][-1] != 3 or row["reply"] != 3:
                continue
            p = weight * runtime.D.LOSS ** (2 - first - second) * (1 - runtime.D.LOSS) ** (2 + first + second)
            exposure += p
            full = row["receipt"]
            price += p * (bank[full] - bank[full & ~4])
    return {"probability_of_addressed_us_reply": float(exposure), "points_at_risk": float(price)}


def run():
    bank_path = c.t.HERE / "numeric-results.json"
    bank = np.array(n.read(bank_path)["score_banks"]["native"])
    config = n.read(o.replan.study.OLD)["training"]["budget_fit"]
    grades = {k: bank[k] for k in range(7) if k != 3}
    results = {}
    for label, (truth, dominant) in a.laws().items():
        for state, prior in (("correct", truth), ("dominant", dominant)):
            opening = o.replan.study.opening(r.f.views(bank)["4"], prior, config)
            apparent, real = o.opening(*opening, prior), o.opening(*opening, truth)
            cache = {}
            for delta in (-7, 0, 7):
                selected = r.evaluate_locked(grades, bank[3] + delta, prior, opening, apparent, cache)
                metrics = {}
                for name in ("interval_team", "interval_fixed"):
                    action = selected[name][1]
                    measured = o.measure(bank, real, truth, opening, action)
                    risk = exposure(truth, opening, action, bank)
                    metrics[name] = {"baseline": measured, "exposure": risk,
                                     "net": {str(rate): measured["net"] - rate * risk["points_at_risk"]
                                             for rate in RATES}}
                results[f"{label}/{state}/{delta}"] = metrics
    summary = {}
    for rate in RATES:
        delta = [row["interval_team"]["net"][str(rate)] - row["interval_fixed"]["net"][str(rate)]
                 for row in results.values()]
        summary[str(rate)] = {"mean_net_margin": sum(delta) / len(delta),
                              "wins": sum(x > 1e-10 for x in delta), "losses": sum(x < -1e-10 for x in delta)}
    paths = (Path(__file__), HERE / "content-protocol.md", bank_path, Path(runtime.__file__))
    return {"summary": summary, "rows": results,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in paths}}


if __name__ == "__main__":
    s.e.emit(run())
