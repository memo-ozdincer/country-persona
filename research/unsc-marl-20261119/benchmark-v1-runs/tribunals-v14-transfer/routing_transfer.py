"""Replay frozen source policies against grounded Resolution 2422 receipt scores."""
import argparse
from itertools import product
from pathlib import Path
from statistics import mean
import sys

import numpy as np

from tribunals_transfer import HERE, NUMBERED, digest, frozen, wire

POLICY = NUMBERED / "myanmar/shift/policy"
sys.path.insert(0, str(POLICY))
import delivery_runtime as runtime
import interval_search as interval

o, f, a = interval.o, interval.f, interval.a
TOL = interval.TOL
SOURCE = {
    "myanmar": (POLICY.parents[1] / "intact-results.json", ("rank_normalized", "bank")),
    "unifil": (NUMBERED / "packed-results.json", ("native", "population", "bank")),
}
INFORMATION = ("correct_mixture", "dominant_only")
MODES = ("interval_team", "interval_fixed")


def source_bank(path, keys):
    result = wire.n.read(path)
    for key in keys:
        result = result[key]
    return np.array(result, dtype=float)


def calibration(bank):
    return {i: value for i, value in enumerate(bank[:7]) if i != 3}


def freeze():
    grandfathered = o.replan.study.OLD
    initializer = wire.n.read(grandfathered)["training"]["budget_fit"]
    contexts = {}
    for (src, (path, keys)), (label, (actual, proxy)), info in product(
            SOURCE.items(), a.laws().items(), INFORMATION):
        prior = actual if info == "correct_mixture" else proxy
        bank = source_bank(path, keys)
        opening = o.replan.study.opening(f.views(bank)["4"], prior, initializer)
        mass = o.opening(*opening, prior)
        policies = interval.evaluate_locked(calibration(bank), bank[3], prior, opening, mass, {})
        contexts[f"{src}/{label}/{info}"] = {
            "source_scores_seen": bank[:7].tolist(),
            "opening": [v.tolist() for v in opening],
            "policies": {mode: {"selection": list(policies[mode][0]),
                                "tables": [v.tolist() for v in policies[mode][1]]}
                         for mode in MODES},
        }
    pins = (Path(__file__), HERE / "routing-protocol.md", POLICY / "interval_search.py",
            POLICY / "block_search.py", POLICY / "policy_search.py", POLICY / "delivery_runtime.py",
            Path(o.__file__), Path(f.__file__), Path(a.__file__),
            Path(o.replan.study.__file__), grandfathered, *(row[0] for row in SOURCE.values()))
    return {"contexts": contexts, "sha256": {file.name: digest(file) for file in pins}}


def stats(points, law, opening, mass, policies):
    measurements = {}
    for name, policy in policies.items():
        output = o.measure(points, mass, law, opening, policy)
        measurements[name] = {k: output[k] for k in ("net", "released", "cost", "queries")}
    return measurements


def run():
    saved = wire.n.read(HERE / "source-policies.json")
    assert saved == freeze()
    fields = wire.n.read(HERE / "results.json")
    rows, banks, witnesses = [], {}, {}
    for kind in ("authored", "model"):
        scores = fields["records"][kind]
        bank = tuple(scores[str(i)]["score"]["released_70"] for i in range(8))
        banks.setdefault(bank, []).append(kind)
    for bank, kinds in banks.items():
        points = np.array(bank, dtype=float)
        for title, settings in saved["contexts"].items():
            _, mixture, info = title.split("/")
            actual, proxy = a.laws()[mixture]
            prior = actual if info == "correct_mixture" else proxy
            opening = tuple(np.array(v) for v in settings["opening"])
            mass, held = o.opening(*opening, prior), o.opening(*opening, actual)
            frozen_tables = {f"source_{mode}": tuple(np.array(v) for v in settings["policies"][mode]["tables"])
                             for mode in MODES}
            oracle = o.controls(points, held, actual, opening)
            fixed = max((v["net"], name) for name, v in oracle.items() if name != "exact_ask_reply")
            cache = {}
            for offset in (-7, 0, 7):
                forecast = float(np.clip(points[3] + offset, 0, 70))
                plans = interval.evaluate_locked(calibration(points), forecast, prior, opening, mass, cache)
                policies = frozen_tables | {f"target_{mode}": plans[mode][1] for mode in MODES}
                assert all(p[0].shape == (8,) and p[1].shape == (8, 4, 4) for p in policies.values())
                measurement = stats(points, actual, opening, held, policies)
                for value in measurement.values():
                    assert value["net"] <= oracle["exact_ask_reply"]["net"] + TOL
                    value["net_over_oracle_fixed"] = value["net"] - fixed[0]
                    value["quality_over_silence"] = value["released"] - oracle["exact_no_request"]["released"]
                rows.append({"bank_arms": kinds, "context": title, "review_offset": offset,
                             "best_oracle_fixed": fixed[1], "oracle_advantage": oracle["exact_ask_reply"]["net"] - fixed[0],
                             "sealed_target_pair_grade": bank[3], "reported_target_pair_grade": forecast,
                             "target_different_from_source": any(
                                 not np.array_equal(src, dst)
                                 for src, dst in zip(policies["source_interval_team"], policies["target_interval_team"],
                                                     strict=True)),
                             "performance": measurement})
                if offset == 0:
                    chosen = {mode: policies[f"target_{mode}"] for mode in MODES}
                    totals, witness = runtime.trace_table(actual, opening, chosen, points)
                    for mode, value in totals.items():
                        reference = measurement[f"target_{mode}"]
                        assert all(np.isclose(reference[k], value[k], atol=TOL, rtol=0) for k in reference if k in value)
                    if witness:
                        witnesses[f"{'-'.join(kinds)}/{title}"] = witness
    return {"banks": [{"points": bank, "arms": kinds} for bank, kinds in banks.items()],
            "summary": summarize(rows), "rows": rows, "delivery_witnesses": witnesses,
            "sha256": {name: digest(HERE / name) for name in ("source-policies.json", "results.json", "routing-protocol.md")}}


def summarize(rows):
    output = {}
    for group in {tuple(row["bank_arms"]) for row in rows}:
        summary = {}
        selected = [row for row in rows if tuple(row["bank_arms"]) == group]
        # Frozen source policies are identical across the target review offsets.
        for label in ("source", "target"):
            subset = selected if label == "target" else [r for r in selected if r["review_offset"] == 0]
            pairs = [(r["performance"][f"{label}_interval_team"], r["performance"][f"{label}_interval_fixed"])
                     for r in subset]
            gains = [team["net"] - fixed["net"] for team, fixed in pairs]
            wins, losses = sum(gain > TOL for gain in gains), sum(gain < -TOL for gain in gains)
            summary[label] = {
                "conditions": len(pairs), "wins": wins, "losses": losses, "ties": len(gains) - wins - losses,
                "mean_gain": mean(gains), "worst_gain": min(gains),
                "mean_gain_over_oracle_fixed": mean(team["net_over_oracle_fixed"] for team, _ in pairs),
                "mean_documentary_gain": mean(team["released"] - fixed["released"] for team, fixed in pairs),
                "below_silence_quality": sum(team["quality_over_silence"] < -TOL for team, _ in pairs),
            }
        output["/".join(group)] = summary
    return dict(sorted(output.items()))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("freeze", "run"))
    frozen.emit({"freeze": freeze, "run": run}[parser.parse_args().mode]())
