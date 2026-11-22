"""Apply the learned reward correction without overwriting live reviewed scores."""
import json
from pathlib import Path
from statistics import mean

import numpy as np

import reward_fit as r
import rollout_fit as s
from routing_transfer import runtime

HERE = Path(__file__).resolve().parent
REVIEWS = (s.TRANSFER / "live-review/separated/atomic/capacity/results.json")


def reconcile(points, law, opening, policy, expected):
    totals, _ = runtime.trace_table(law, opening, {"interval_team": policy, "interval_fixed": policy}, points)
    for field in ("released", "cost", "net", "queries"):
        assert abs(totals["interval_team"][field] - expected[field]) <= 1e-9


def run():
    study = s.wire.n.read(HERE / "results.json")
    model = s.wire.n.read(HERE / "reward-results.json")
    cases = s.wire.n.read(HERE / "plan.json")["test_banks"]
    reviews = s.wire.n.read(REVIEWS)
    weights, strength = np.array(model["weights"]), model["selected_strength"]
    init = s.wire.n.read(s.INITIAL)["training"]["budget_fit"]
    key_fields = ("case", "law", "information", "review_offset")
    cases_index = {}
    laws = s.a.laws()
    for raw, adjusted in zip(study["rows"], model["rows"], strict=True):
        key = tuple(raw[field] for field in key_fields)
        assert key == tuple(adjusted[field] for field in key_fields)
        case, label, info, offset = key
        points = np.array(cases[case], dtype=float)
        actual, proxy = laws[label]
        declared = actual if info == "exact" else proxy
        opening, mass, forecast = s.context(points, np.clip(points[3] + offset, 0, 70), declared, init)
        assert [item.tolist() for item in opening] == raw["opening"]
        learned_policy = tuple(np.array(v) for v in raw["learned_policy"])
        reconcile(points, actual, opening, learned_policy, raw["outcomes"]["learned"])
        adjusted_policy = s.deploy(r.corrected(forecast, weights, strength), mass, r.NO_FIT)
        reconcile(points, actual, opening, adjusted_policy, adjusted["outcomes"]["selected"])
        cases_index[key] = (raw, adjusted, points, actual, declared, opening)
    rows = []
    for row in reviews["rows"]:
        case, label, info, offset = (row[key] for key in ("case", "law", "prior_information", "offset"))
        original, adjusted, points, true, declared, opening = cases_index[case, label, info, offset]
        reviewed = row["capacity"]["factored_agreement"]
        grade = reviewed["grade"]
        assert grade is not None
        shown_opening, mass, forecast = s.context(points, grade, declared, init)
        assert all(np.array_equal(before, after) for before, after in zip(opening, shown_opening, strict=True))
        free = r.corrected(forecast, weights, strength)
        protected = free.copy()
        protected[3] = grade
        methods = {"learned_noisy": adjusted["outcomes"]["selected"], "reviewed_search": reviewed["metrics"]}
        for key, vector in (("review_only", forecast), ("review_plus_inference", protected),
                            ("review_with_overwrite", free)):
            methods[key] = s.metric(points, true, opening, s.deploy(vector, mass, r.NO_FIT))
        rows.append({k: row[k] for k in ("case", "law", "prior_information", "offset")} |
                    {"verified_pair_score": grade, "overwritten_score": float(free[3]),
                     "silence_quality": original["silence_quality"], "outcomes": methods})
    refs = ("learned_noisy", "review_only", "review_plus_inference", "review_with_overwrite", "reviewed_search")
    summary = {name: {
        "below_silence": sum(row["outcomes"][name]["released"] < row["silence_quality"] - 1e-9 for row in rows),
        "mean_net": mean(row["outcomes"][name]["net"] for row in rows),
        "versus_review_only": s.compare([row["outcomes"][name]["net"] - row["outcomes"]["review_only"]["net"] for row in rows]),
    } for name in refs}
    pins = (Path(__file__), HERE / "reviewed-protocol.md", HERE / "plan.json", HERE / "results.json",
            HERE / "reward-results.json", REVIEWS, Path(runtime.__file__))
    assert len(rows) == 23
    return {"exhaustive_dispatch_reconciliations": len(cases_index) * 2, "summary": summary,
            "rows": rows, "sha256": {str(path.resolve().relative_to(s.TRIB.parents[1])): s.digest(path) for path in pins}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
