"""Cross frozen score corrections while holding the policy optimizer fixed."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from statistics import mean
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
RUNS = PARENT.parent
sys.path.insert(0, str(PARENT))
import reward_fit as reward
import rollout_fit as s
from routing_transfer import runtime

READ = s.wire.n.read
SOURCE = PARENT / "writer-transfer/results.json"
SCORES = RUNS / "tolerance-2686-transfer/scoped-writer/scores.json"
REFERENCE = PARENT / "reward-results.json"
LOCKED = PARENT / "plan.json"


def plan():
    inputs = {"fit": REFERENCE, "train_plan": LOCKED, "openings": s.INITIAL, "held": SOURCE,
              "writer_scores": SCORES, "program": Path(__file__), "protocol": HERE / "protocol.md",
              "planner": Path(s.o.__file__), "dispatcher": Path(runtime.__file__)}
    return {"inputs_sha256": {name: s.digest(file) for name, file in inputs.items()},
            "variants": ["nominal", "learned_pair", "learned_full", "learned_both",
                         "upward_learned_pair", "half_additive_pair", "constant_up_pair"],
            "offsets": [-7, 0, 7]}


def options(nominal, weights, strength):
    fit = reward.corrected(nominal, weights, strength)
    pair = nominal[3]
    additive = nominal[1] + nominal[2] - nominal[0]
    replacements = {
        "nominal": (pair, nominal[7]),
        "learned_pair": (fit[3], nominal[7]),
        "learned_full": (pair, fit[7]),
        "learned_both": (fit[3], fit[7]),
        "upward_learned_pair": (max(float(pair), float(fit[3])), nominal[7]),
        "half_additive_pair": ((pair + additive) / 2, nominal[7]),
        "constant_up_pair": (pair + 3.5, nominal[7]),
    }
    for name, grades in replacements.items():
        values = nominal.copy()
        values[[3, 7]] = np.clip(grades, 0, 70)
        assert np.array_equal(values[[0, 1, 2, 4, 5, 6]], nominal[[0, 1, 2, 4, 5, 6]])
        yield name, values


def summarize(rows, variants):
    output = {}
    for tag, group in (
        ("archive", [r for r in rows if r["case"] not in {"scoped", "verbatim"}]),
        *((name, [r for r in rows if r["case"] == name]) for name in sorted({r["case"] for r in rows})),
    ):
        sections = {"all": group} | {
            str(offset): [r for r in group if r["review_offset"] == offset] for offset in (-7, 0, 7)}
        output[tag] = {}
        for label, subset in sections.items():
            result = {}
            for arm in variants:
                values = [r["outcomes"][arm] for r in subset]
                baseline = [r["outcomes"]["nominal"] for r in subset]
                result[arm] = {
                    "net_vs_nominal": s.compare([a["net"] - b["net"] for a, b in zip(values, baseline, strict=True)]),
                    "net_vs_fixed": s.compare([a["net"] - r["matched_fixed"] for a, r in zip(values, subset, strict=True)]),
                    "net_vs_robust": s.compare([a["net"] - r["robust"] for a, r in zip(values, subset, strict=True)]),
                    "mean_released_delta": mean(a["released"] - b["released"] for a, b in zip(values, baseline, strict=True)),
                    "mean_cost_delta": mean(a["cost"] - b["cost"] for a, b in zip(values, baseline, strict=True)),
                    "below_silence": sum(a["released"] < r["silence"] - 1e-9 for a, r in zip(values, subset, strict=True)),
                    "changed_actions": sum(r["outcomes"][arm]["action_digest"] != r["outcomes"]["nominal"]["action_digest"]
                                           for r in subset),
                }
            output[tag][label] = result
    return output


def run():
    locked = plan()
    assert locked == READ(HERE / "plan.json")
    fitted = READ(REFERENCE)
    weights, strength = np.array(fitted["weights"]), fitted["selected_strength"]
    init = READ(s.INITIAL)["training"]["budget_fit"]
    banks = READ(LOCKED)["test_banks"] | READ(SCORES)["banks"]
    laws = s.a.laws()
    rows = []
    replays = 0
    for row in READ(SOURCE)["rows"]:
        case, law_id, info, offset = [row[k] for k in ("case", "law", "prior_information", "review_offset")]
        points = np.array(banks[case], dtype=float)
        law, proxy = laws[law_id]
        announced = law if info == "exact" else proxy
        opening, mass, nominal = s.context(points, np.clip(points[3] + offset, 0, 70), announced, init)
        assert [v.tolist() for v in opening] == row["opening"]
        policies, forecasts = {}, {}
        for arm, forecast in options(nominal, weights, strength):
            forecasts[arm] = forecast.tolist()
            policies[arm] = s.o.exact_parts(mass, forecast)["exact_ask_reply"]
        assert list(policies) == locked["variants"]
        assert [v.tolist() for v in policies["nominal"]] == row["policies"]["exact_forecast"]
        actual = s.o.controls(points, s.o.opening(*opening, law), law, opening)
        # The dispatcher only uses these two names to look for a legacy witness.
        expanded = policies | {"interval_team": policies["nominal"], "interval_fixed": policies["nominal"]}
        branch, _ = runtime.trace_table(law, opening, expanded, points)
        outcomes = {}
        for arm, policy in policies.items():
            value = s.metric(points, law, opening, policy)
            checked = branch[arm]
            assert abs(sum(checked["receipt_mass"]) - 1) <= 1e-9
            assert all(abs(checked[key] - val) <= 1e-9 for key, val in value.items())
            assert value["net"] <= actual["exact_ask_reply"]["net"] + 1e-9
            table = [v.tolist() for v in policy]
            key = sha256(json.dumps(table, separators=(",", ":")).encode()).hexdigest()
            outcomes[arm] = value | {"action_digest": key, "receipt_mass": checked["receipt_mass"]}
            replays += 1
        baseline = row["outcomes"]["exact_forecast"]
        assert all(abs(outcomes["nominal"][key] - baseline[key]) <= 1e-9
                   for key in ("released", "cost", "net", "queries"))
        rows.append({"case": case, "law": law_id, "prior_information": info, "review_offset": offset,
                     "forecast_3_and_7": {arm: [v[3], v[7]] for arm, v in forecasts.items()},
                     "silence": float(actual["exact_no_request"]["released"]),
                     "matched_fixed": row["outcomes"]["interval_fixed"]["net"],
                     "robust": row["outcomes"]["interval_team"]["net"], "outcomes": outcomes})
    assert len(rows) == 126 and set(Counter(r["case"] for r in rows).values()) == {18}
    assert replays == 126 * len(locked["variants"])
    return {"rows": rows, "summary": summarize(rows, locked["variants"]),
            "independent_policy_replays": replays, "plan_sha256": s.digest(HERE / "plan.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run"))
    print(json.dumps({"plan": plan, "run": run}[parser.parse_args().mode](), indent=2))
