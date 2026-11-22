"""Replay frozen forecast arms and same-information fixed on the new transfer."""
import argparse
from itertools import product
import json
from pathlib import Path
from statistics import mean
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
OTHER = HERE.parent / "cooperative-rollout-fit/forecast-mechanism"
sys.path.insert(0, str(OTHER))
from forecast_mechanism import REFERENCE, READ, options, runtime, s

MODES = ("nominal", "learned_pair", "half_additive_pair")


def plan():
    inputs = (Path(__file__), HERE / "routing-protocol.md", HERE / "plan.json", REFERENCE,
              OTHER / "forecast_mechanism.py", s.INITIAL, Path(runtime.__file__), Path(s.o.__file__))
    return {"inputs_sha256": {path.name: s.digest(path) for path in inputs},
            "arms": [*MODES, "fixed"], "offsets": [-7, 0, 7]}


def run():
    locked = plan()
    assert locked == READ(HERE / "routing-plan.json")
    trained = READ(REFERENCE)
    weights, strength = np.array(trained["weights"]), trained["selected_strength"]
    init = READ(s.INITIAL)["training"]["budget_fit"]
    banks = READ(HERE / "scores.json")["banks"]
    output = {}
    for name, bank in banks.items():
        points = np.array(bank, dtype=float)
        rows = []
        for (label, (law, proxy)), info, offset in product(
                s.a.laws().items(), ("exact", "dominant_only"), locked["offsets"]):
            shown = law if info == "exact" else proxy
            reported = float(np.clip(points[3] + offset, 0, 70))
            opening, mass, nominal = s.context(points, reported, shown, init)
            grades = {k: f for k, f in options(nominal, weights, strength) if k in MODES}
            policies = {k: s.o.exact_parts(mass, f)["exact_ask_reply"] for k, f in grades.items()}
            fixed = [(q, s.o.choose_response(q, mass, nominal)) for q in s.FIXED]
            policies["fixed"] = max(fixed, key=lambda arm: s.metric(nominal, shown, opening, arm)["net"])
            actual = s.o.controls(points, s.o.opening(*opening, law), law, opening)
            enumerated, _ = runtime.trace_table(law, opening, policies | {
                "interval_team": policies["nominal"], "interval_fixed": policies["fixed"]}, points)
            outcome = {}
            for mode, arm in policies.items():
                result = s.metric(points, law, opening, arm)
                assert all(abs(value - enumerated[mode][k]) <= 1e-9 for k, value in result.items())
                assert abs(sum(enumerated[mode]["receipt_mass"]) - 1) <= 1e-9
                assert result["net"] <= actual["exact_ask_reply"]["net"] + 1e-9
                outcome[mode] = result
            rows.append({"law": label, "information": info, "review_offset": offset, "reported": reported,
                         "forecast_pair": {k: float(f[3]) for k, f in grades.items()},
                         "informed_silence": float(actual["exact_no_request"]["released"]),
                         "outcomes": outcome, "policies": {k: [v.tolist() for v in arm] for k, arm in policies.items()},
                         "receipts": {k: enumerated[k]["receipt_mass"] for k in policies}})
        assert len(rows) == 18
        summary = {}
        for mode in MODES:
            outcomes = [row["outcomes"][mode] for row in rows]
            summary[mode] = {
                "vs_nominal": s.compare([out["net"] - row["outcomes"]["nominal"]["net"]
                                         for out, row in zip(outcomes, rows, strict=True)]),
                "vs_fixed": s.compare([out["net"] - row["outcomes"]["fixed"]["net"]
                                       for out, row in zip(outcomes, rows, strict=True)]),
                "mean_released": mean(out["released"] for out in outcomes),
                "below_silence": sum(out["released"] < row["informed_silence"] - 1e-9
                                     for out, row in zip(outcomes, rows, strict=True)),
            }
        output[name] = {"summary": summary, "rows": rows}
    return {"banks": banks, "results": output, "policy_replays": sum(len(v["rows"]) * 4 for v in output.values()),
            "sha256": {name: s.digest(HERE / name) for name in ("routing-plan.json", "scores.json")}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run"))
    print(json.dumps({"plan": plan, "run": run}[parser.parse_args().mode](), indent=2))
