"""Cross calibrated routers with original and revised final-writer outcomes."""
import json
from pathlib import Path
from statistics import mean
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
sys.path.insert(0, str(PARENT))
from route_tolerance import base, fitted, interval, o, ref
from routing_transfer import runtime

ARMS = ("interval_team", "interval_fixed")


def run():
    banks = {key: base.n.read(path) for key, path in (
        ("original", PARENT / "route-results.json"), ("revised", HERE / "route-results.json"))}
    before, after = banks.values()
    init = base.n.read(fitted.INITIAL)["training"]["budget_fit"]
    scores = {name: np.array(route["score_bank"]) for name, route in banks.items()}
    singleton = {name: interval.s.t.cal.estimated(values) for name, values in scores.items()}
    rows = []
    for i, (old, new) in enumerate(zip(before["rows"], after["rows"], strict=True)):
        keys = ("law", "prior_information", "review_offset")
        case = {k: old[k] for k in keys}
        assert case == {k: new[k] for k in keys}
        law, proxy = fitted.a.laws()[case["law"]]
        shown = law if case["prior_information"] == "exact" else proxy
        values = {}
        for source, archived in (("original", old), ("revised", new)):
            opening = o.replan.study.opening(singleton[source], shown, init)
            row = {}
            for arm in ARMS:
                policy = archived["choices"][arm]
                table = tuple(np.array(v) for v in policy["deployed_actions"])
                distribution = None
                effects = {}
                for target, values_bank in scores.items():
                    if policy["stochastic"]:
                        out = ref.replay(law, opening, table, values_bank)
                    else:
                        audit, _ = runtime.trace_table(law, opening, {"interval_team": table, "interval_fixed": table}, values_bank)
                        out = audit["interval_team"]
                    if source == target:
                        assert all(abs(out[name] - archived["outcomes"][arm][name]) < 1e-9
                                   for name in ("released", "cost", "net", "queries"))
                    if distribution is not None:
                        assert np.allclose(distribution, out["receipt_mass"], atol=1e-12, rtol=0)
                    distribution = [float(mass) for mass in out["receipt_mass"]]
                    effects[target] = {key: float(out[key]) for key in ("released", "net", "cost", "queries")}
                assert abs(sum(distribution) - 1) < 1e-9
                row[arm] = {"outcomes": effects, "probability_uk": sum(distribution[4:]),
                            "probability_full": distribution[7], "receipt_mass": distribution}
            values[source] = row
        rows.append(case | {"scenarios": values})
    summary = {}
    for source in banks:
        variants = {}
        for target in banks:
            team = [r["scenarios"][source][ARMS[0]] for r in rows]
            fixed = [r["scenarios"][source][ARMS[1]] for r in rows]
            deltas = [a["outcomes"][target]["net"] - b["outcomes"][target]["net"] for a, b in zip(team, fixed)]
            variants[target] = {
                "team_vs_matched_fixed": fitted.compare(deltas),
                "team_mean_release": mean(r["outcomes"][target]["released"] for r in team),
                "team_mean_net": mean(r["outcomes"][target]["net"] for r in team),
                "mean_uk_delivery": mean(r["probability_uk"] for r in team),
                "mean_full_delivery": mean(r["probability_full"] for r in team),
            }
        summary[source] = variants
    assert len(rows) == 18
    pins = (Path(__file__).resolve(), HERE / "routing-protocol.md", PARENT / "route-results.json",
            HERE / "route-results.json", Path(runtime.__file__))
    return {"summary": summary, "branched_policy_score_checks": len(rows) * len(ARMS) * len(banks),
            "rows": rows, "sha256": {str(p.relative_to(PARENT.parents[1])): fitted.digest(p) for p in pins}}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
