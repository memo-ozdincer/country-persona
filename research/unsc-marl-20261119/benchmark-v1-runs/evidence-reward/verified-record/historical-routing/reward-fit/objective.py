"""Score every policy in raw released points minus the same communication costs."""
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import replan

h, fit, D, R = replan.h, replan.fit, replan.D, replan.routed
e, opening = h.e, replan.joint.opening


def payoff(points):
    return np.broadcast_to((D.LAST @ points - D.SEND_COST)[:, None, :], (8, 4, 4))


def choose_response(q, mass, points):
    observed = fit.heard(D.one_hot(q))
    value = np.einsum("rbm,mt,mtc->rbtc", mass, observed, payoff(points))
    return np.where(D.FINAL_LEGAL, value, -np.inf).argmax(-1)


def exact_parts(mass, points):
    observed = fit.heard(D.one_hot(fit.MAPS))
    value = np.einsum("rbm,pmt,mtc->prbtc", mass, observed, payoff(points))
    legal = np.where(D.FINAL_LEGAL[None], value, -np.inf)
    net = legal.max(-1).sum((1, 2, 3)) - D.QUERY_COST[fit.MAPS] @ mass.sum((0, 1))
    best = int(net.argmax())
    return {"exact_ask_reply": (fit.MAPS[best], legal[best].argmax(-1)),
            "exact_no_request": (fit.MAPS[0], legal[0].argmax(-1))}


def measure(points, mass, prior, openers, pair):
    # The shared helper returns released points, cost and receipt mass
    # independently of its optional complete-record bonus.
    stats = fit.measure(pair, openers, mass, prior, points, fit.PERFECT)
    return {"released": stats["guarded_points"], "cost": stats["cost"],
            "net": stats["guarded_points"] - stats["cost"],
            "strict": stats["strict_complete"], "receipt_mass": stats["receipt_mass"],
            "queries": float(mass.sum((0, 1)) @ (pair[0] != 0))}


def historical():
    artifact = e.read(HERE.parent / "results.json")
    known = e.read(h.ARCHIVE / "forecast.json")["budgets"]["70"]["laws"]
    for endpoint in ("v1.2", "compact"):
        points = np.array([artifact["records"][f"{endpoint}/{mask}"]["released_70"] for mask in range(8)])
        surface = "native_compiled_v1.2" if endpoint == "v1.2" else "compact_v1.2"
        for label, law in R.TEST_PRIORS.items():
            openers = tuple(np.array(vec) for vec in known[label]["openers"])
            mass = opening(*openers, law)
            archived = artifact["expected"][label][surface]
            yield endpoint, label, points, law, openers, mass, archived


def controls(points, mass, law, openers):
    table = exact_parts(mass, points)
    for field in range(1, 4):
        q = np.where(D.CHAIR_LEGAL[:, field], field, 0)
        table[f"fixed_{field}_exact_reply"] = (q, choose_response(q, mass, points))
    return {name: measure(points, mass, law, openers, pair) for name, pair in table.items()}


if __name__ == "__main__":
    report = {}
    for endpoint, label, points, law, openers, mass, archived in historical():
        corrected = controls(points, mass, law, openers)
        assert all(old["net"] <= corrected["exact_ask_reply"]["net"] + 1e-10 for old in archived.values())
        report.setdefault(endpoint, {})[label] = corrected
    e.emit(report)
