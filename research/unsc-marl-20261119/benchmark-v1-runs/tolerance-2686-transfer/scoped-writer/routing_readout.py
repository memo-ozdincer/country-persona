"""Independently replay matched routing policies on generated writer banks."""
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


def run():
    original = PARENT / "route-results.json"
    paths = {"original": original, **{name: HERE / f"{name}-route.json" for name in ("scoped", "verbatim")}}
    reports = {name: base.n.read(path) for name, path in paths.items()}
    init = base.n.read(fitted.INITIAL)["training"]["budget_fit"]
    table = []
    for original_row, scoped, verbatim in zip(*(r["rows"] for r in reports.values()), strict=True):
        condition = {k: original_row[k] for k in ("law", "prior_information", "review_offset")}
        law, proxy = fitted.a.laws()[condition["law"]]
        announced = law if condition["prior_information"] == "exact" else proxy
        row = {}
        for name, expected in zip(reports, (original_row, scoped, verbatim), strict=True):
            assert all(expected[k] == v for k, v in condition.items())
            bank = np.array(reports[name]["score_bank"], dtype=float)
            opening = o.replan.study.opening(interval.s.t.cal.estimated(bank), announced, init)
            arms = {}
            for mode in ("interval_team", "interval_fixed"):
                saved = expected["choices"][mode]
                policy = tuple(np.asarray(v) for v in saved["deployed_actions"])
                if saved["stochastic"]:
                    out = ref.replay(law, opening, policy, bank)
                else:
                    replay, _ = runtime.trace_table(law, opening, {"interval_team": policy, "interval_fixed": policy}, bank)
                    out = replay["interval_team"]
                assert all(abs(out[m] - expected["outcomes"][mode][m]) <= 1e-9
                           for m in ("released", "cost", "net", "queries"))
                mass = [float(x) for x in out["receipt_mass"]]
                assert abs(sum(mass) - 1) <= 1e-9
                arms[mode] = {k: float(out[k]) for k in ("released", "cost", "net", "queries")} | {
                    "receipt_mass": mass, "uk_receipt": sum(mass[4:]), "full_receipt": mass[7]}
            row[name] = arms
        table.append(condition | {"results": row})
    summary = {}
    for name in reports:
        choices = [r["results"][name] for r in table]
        summary[name] = {
            "team_over_fixed": fitted.compare([r["interval_team"]["net"] - r["interval_fixed"]["net"] for r in choices]),
            "team_mean_release": mean(r["interval_team"]["released"] for r in choices),
            "fixed_mean_release": mean(r["interval_fixed"]["released"] for r in choices),
            "team_mean_uk_receipt": mean(r["interval_team"]["uk_receipt"] for r in choices),
            "team_mean_full_receipt": mean(r["interval_team"]["full_receipt"] for r in choices),
        }
    assert len(table) == 18
    return {"rows": table, "summary": summary, "policy_checks": len(table) * len(reports) * 2,
            "sha256": {str(p.relative_to(PARENT.parents[1])): fitted.digest(p)
                       for p in (Path(__file__).resolve(), *paths.values(), Path(runtime.__file__))}}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
