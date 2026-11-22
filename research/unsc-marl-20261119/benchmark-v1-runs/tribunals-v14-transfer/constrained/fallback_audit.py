"""Compare conditional stochastic policy updates on all 21 recorded settings."""
from hashlib import sha256
import json
from pathlib import Path
from statistics import mean

import numpy as np

from solve_floor import D, EPS, a, forecast_data, o, vertices, wire
from mixed_floor import best_admissible, best_fixed_tradeoffs, provider, score

HERE = Path(__file__).resolve().parent
TEAM, FIXED = "interval_team", "interval_fixed"


def summary(rows, key):
    pairs = [(r[key][TEAM], r[key][FIXED]) for r in rows]
    margins = [float(team["net"] - fixed["net"]) for team, fixed in pairs]
    wins = sum(v > EPS for v in margins)
    losses = sum(v < -EPS for v in margins)
    return {"settings": len(pairs), "wins": wins, "losses": losses, "ties": len(pairs) - wins - losses,
            "mean_net_margin": mean(margins),
            "mean_net_over_exact_fixed": mean(team["net_over_oracle_fixed"] for team, _ in pairs),
            "below_silence": sum(float(team["quality_over_silence"]) < -EPS for team, _ in pairs)}


def run():
    transfer = HERE.parent
    routed = wire.n.read(transfer / "routing-results.json")
    held_points = np.array(routed["banks"][0]["points"], dtype=float)
    settings = wire.n.read(transfer / "source-policies.json")["contexts"]
    original = wire.n.read(transfer / "prior-results.json")
    fixed_maps = np.array([np.where(D.CHAIR_LEGAL[:, target], target, 0) for target in range(4)])
    reported = {(r["context"], r["review_offset"]): r["reported_target_pair_grade"] for r in routed["rows"]}
    rows = []
    for row in original["rows"]:
        context = row["contexts"][0]
        _, mixture, information = context.split("/")
        offset = row["review_offset"]
        archived = row["prior_envelope"]
        updated = dict(archived)
        status = {mode: "retained" for mode in updated}
        details = {}
        failed = [mode for mode, cert in row["qualification"].items() if cert["eligible_candidates"] == 0]
        if failed:
            assert information == "dominant_only"
            opening = tuple(np.array(t) for t in settings[context]["opening"])
            scenarios = forecast_data(held_points, reported[context, offset], vertices(mixture), opening)
            true, _ = a.laws()[mixture]
            controls = o.controls(held_points, o.opening(*opening, true), true, opening)
            informed = {"silence": controls["exact_no_request"]["released"],
                        "fixed_net": max(v["net"] for name, v in controls.items() if name != "exact_ask_reply")}
            for mode in failed:
                maps = o.fit.MAPS if mode == TEAM else fixed_maps
                choice = best_admissible(maps, scenarios)
                qualified = choice is not None
                if not qualified:
                    if mode == TEAM:
                        status[mode] = "retained_after_infeasible_search"
                        continue
                    choice = best_fixed_tradeoffs(maps, scenarios)["fixed_best_quality"]
                q, coeffs, sol = choice
                detail = score("team_at_floor" if qualified else mode, provider(q, coeffs, sol),
                               coeffs, sol, opening, scenarios, true, held_points, informed)
                status[mode] = "qualified_stochastic" if qualified else "best_stochastic_quality"
                outcome = dict(detail["held"])
                outcome["net_over_oracle_fixed"] = outcome.pop("net_over_exact_fixed")
                updated[mode] = outcome
                details[mode] = detail
        rows.append({"contexts": row["contexts"], "review_offset": offset, "status": status,
                     "old": archived, "updated": updated, "details": details})
    assert len(rows) == 21
    pins = (Path(__file__), HERE / "fallback-protocol.md", HERE / "mixed_floor.py",
            HERE / "solve_floor.py", *(transfer / name for name in
                ("prior-results.json", "routing-results.json", "source-policies.json")))
    return {"summary": {key: summary(rows, key) for key in ("old", "updated")},
            "rows": rows, "sha256": {file.name: sha256(file.read_bytes()).hexdigest() for file in pins}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
