"""Replay the frozen routing families on the prospective free-form receipt bank."""
import argparse
import importlib.util
from itertools import product
import json
from pathlib import Path
from statistics import mean
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "cooperative-rollout-fit"))
import reward_fit as reward
import rollout_fit as fitted

base, o, interval = fitted.wire, fitted.o, fitted.interval
TRIB = HERE.parent / "tribunals-v14-transfer"
cross = TRIB / "constrained/transfer/transfer.py"
spec = importlib.util.spec_from_file_location("tolerance_routing_reference", cross)
ref = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ref)


def run(score_path):
    document = base.n.read(score_path)
    bank = np.array(document["score_bank"], dtype=float)
    assumed = bank.copy()
    assumed[[3, 7]] = np.nan
    solo = fitted.interval.s.t.cal.estimated(assumed)
    init = base.n.read(fitted.INITIAL)["training"]["budget_fit"]
    trained = base.n.read(HERE.parent / "cooperative-rollout-fit/reward-results.json")
    weights, scale = np.array(trained["weights"]), trained["selected_strength"]
    rows = []
    for (tag, (actual, proxy)), info in product(fitted.a.laws().items(), ("exact", "dominant_only")):
        shown = actual if info == "exact" else proxy
        priors = [shown] if info == "exact" else ref.vertices(tag)
        opening = o.replan.study.opening(solo, shown, init)
        mass = o.opening(*opening, shown)
        oracles = o.controls(bank, o.opening(*opening, actual), actual, opening)
        shared = {}
        for offset in (-7, 0, 7):
            effect = float(np.clip(bank[3] + offset, 0, 70))
            old, values = ref.pick(assumed, effect, priors, opening, shared)
            results, choices = {}, {}
            for mode, (selection, policy, accepted) in old.items():
                mixed = None
                qualification = None
                if not accepted:
                    scenarios = ref.forecast_data(assumed, effect, priors, opening)
                    maps = o.fit.MAPS if mode == ref.TEAM else ref.FIXED_MAPS
                    mixed, _, proof = ref.full_search(maps, scenarios)
                    qualification = {"qualifying_maps": proof["qualifying_relaxed_maps"]}
                    if mode == ref.FIXED and mixed is None:
                        q, c, x = ref.best_fixed_tradeoffs(maps, scenarios)["fixed_best_quality"]
                        mixed = ref.provider(q, c, x)
                results[mode] = ref.held(policy if mixed is None else mixed, bank, actual, opening, oracles,
                                         stochastic=mixed is not None)
                choices[mode] = {"catalog_choice": selection, "catalog_eligible": int(accepted),
                                 "expanded": qualification,
                                 "deployed_actions": [v.tolist() for v in (policy if mixed is None else mixed)],
                                 "stochastic": mixed is not None}
            forecast = interval.forecasts({i: assumed[i] for i in (0, 1, 2, 4, 5, 6)}, effect)
            for name, value in (("neutral", forecast), ("learned_forecast", reward.corrected(forecast, weights, scale))):
                results[name] = ref.held(fitted.deploy(value, mass, reward.NO_FIT), bank, actual, opening, oracles)
            rows.append({"law": tag, "prior_information": info, "review_offset": offset, "forecast": forecast.tolist(),
                         "true_silence": oracles["exact_no_request"]["released"],
                         "oracle_adaptive": oracles["exact_ask_reply"]["net"], "outcomes": results, "choices": choices})
    summary = {}
    for mode in (ref.TEAM, "neutral", "learned_forecast"):
        values = [row["outcomes"][mode] for row in rows]
        summary[mode] = {
            "net_vs_matched_fixed": fitted.compare([
                value["net"] - row["outcomes"][ref.FIXED]["net"] for value, row in zip(values, rows, strict=True)]),
            "net_vs_informed_fixed": fitted.compare([value["over_informed_fixed"] for value in values]),
            "below_silence": sum(value["over_informed_silence_quality"] < -ref.EPS for value in values),
            "mean_released": mean(value["released"] for value in values),
            "mean_queries": mean(value["queries"] for value in values),
        }
    summary["learned_over_neutral"] = fitted.compare([r["outcomes"]["learned_forecast"]["net"] -
                                                      r["outcomes"]["neutral"]["net"] for r in rows])
    assert len(rows) == 18
    pins = (Path(__file__).resolve(), HERE / "protocol.md", score_path, cross,
            HERE.parent / "cooperative-rollout-fit/reward-results.json")
    return {"score_bank": bank.tolist(), "summary": summary, "rows": rows,
            "sha256": {str(path.relative_to(HERE.parents[1])): fitted.digest(path) for path in pins}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scores", type=Path, default=HERE / "scores.json")
    print(json.dumps(run(parser.parse_args().scores.resolve()), ensure_ascii=False, indent=2))
