"""Dispatch the stored policies over all hidden inventory and delivery branches."""
import json
from pathlib import Path
from statistics import mean

import numpy as np

from route_tolerance import HERE, base, fitted, interval, o, ref
from routing_transfer import runtime


def run():
    init = base.n.read(fitted.INITIAL)["training"]["budget_fit"]
    replays = {}
    for file in (HERE / "route-results.json", HERE / "assembly-route.json"):
        record = base.n.read(file)
        points = np.array(record["score_bank"])
        singleton = interval.s.t.cal.estimated(points)
        rows = []
        for condition in record["rows"]:
            law, proxy = fitted.a.laws()[condition["law"]]
            prior = law if condition["prior_information"] == "exact" else proxy
            opening = o.replan.study.opening(singleton, prior, init)
            receipts = {}
            for name, setup in condition["choices"].items():
                arm = tuple(np.array(item) for item in setup["deployed_actions"])
                if setup["stochastic"]:
                    observed = ref.replay(law, opening, arm, points)
                else:
                    observed, _ = runtime.trace_table(law, opening,
                        {"interval_team": arm, "interval_fixed": arm}, points)
                    observed = observed["interval_team"]
                expected = condition["outcomes"][name]
                assert all(abs(observed[key] - expected[key]) <= 1e-9 for key in ("released", "cost", "net", "queries"))
                outcomes = np.array(observed["receipt_mass"])
                assert abs(outcomes.sum() - 1) <= 1e-9
                receipts[name] = {"probability_of_uk_note": float(outcomes[4:].sum()),
                                  "probability_of_full_receipt": float(outcomes[-1]),
                                  "probability_of_zero_score": float(outcomes[points == 0].sum())}
            rows.append({key: condition[key] for key in ("law", "prior_information", "review_offset")} | {"metrics": receipts})
        replays[file.name] = {
            "matched_policy_checks": sum(len(row["metrics"]) for row in rows),
            "mean": {arm: {metric: mean(row["metrics"][arm][metric] for row in rows)
                           for metric in rows[0]["metrics"][arm]} for arm in rows[0]["metrics"]},
            "rows": rows,
        }
    pins = (Path(__file__).resolve(), HERE / "route-results.json", HERE / "assembly-route.json", Path(runtime.__file__))
    return {"dispatch": replays, "sha256": {p.name: fitted.digest(p) for p in pins}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
