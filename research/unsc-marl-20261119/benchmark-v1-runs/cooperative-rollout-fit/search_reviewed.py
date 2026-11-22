"""Test the learned full-receipt forecast under the same robust planner."""
import json
from pathlib import Path
from statistics import mean
import sys
from unittest.mock import patch

import numpy as np

import reward_fit as r
import rollout_fit as s

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(s.TRANSFER / "live-review"))
import grade_and_route as reviewed


def run():
    inputs = s.wire.n.read(HERE / "reviewed-results.json")
    fitted = s.wire.n.read(HERE / "reward-results.json")
    banks = s.wire.n.read(HERE / "plan.json")["test_banks"]
    old = s.wire.n.read(s.TRANSFER / "results.json")["rows"]
    weights = np.array(fitted["weights"])
    scale = fitted["selected_strength"]
    keys = ("case", "law", "prior_information", "review_offset")
    source = {tuple(row[k] for k in keys): row for row in old}
    exact_forecasts = s.interval.forecasts

    def changed(calibrated, noisy):
        base = exact_forecasts(calibrated, noisy)
        updated = base.copy()
        updated[7] = r.corrected(base, weights, scale)[7]
        assert np.array_equal(updated[:7], base[:7])
        return updated

    output, memo = [], {}
    for item in inputs["rows"]:
        key = (item["case"], item["law"], item["prior_information"], item["offset"])
        points = np.array(banks[key[0]], dtype=float)
        grade = item["verified_pair_score"]
        cache_key = (*key[:3], grade)
        if cache_key not in memo:
            ref = reviewed.reroute(source[key], points, grade)
            with patch.object(s.interval, "forecasts", changed):
                updated = reviewed.reroute(source[key], points, grade)
            memo[cache_key] = ref, updated
        ref, updated = memo[cache_key]
        for field, target in item["outcomes"]["reviewed_search"].items():
            assert abs(ref[field] - target) < 1e-9
        output.append({k: item[k] for k in ("case", "law", "prior_information", "offset", "silence_quality")} |
                      {"original_search": ref, "learned_forecast_search": updated})
    delta = [row["learned_forecast_search"]["net"] - row["original_search"]["net"] for row in output]
    release = [row["learned_forecast_search"]["released"] - row["original_search"]["released"] for row in output]
    pins = (Path(__file__).resolve(), HERE / "search-protocol.md", HERE / "reviewed-results.json",
            HERE / "reward-results.json", Path(reviewed.__file__), s.TRANSFER / "results.json")
    return {"summary": {"net_change": s.compare(delta), "mean_release_change": mean(release),
                        "below_silence": sum(row["learned_forecast_search"]["released"] < row["silence_quality"] - 1e-9
                                             for row in output)},
            "policy_contexts_recomputed": len(memo), "rows": output,
            "sha256": {str(path.resolve().relative_to(s.TRIB.parents[1])): s.digest(path) for path in pins}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
