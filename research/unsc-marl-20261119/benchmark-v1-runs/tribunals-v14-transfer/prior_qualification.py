"""Qualify model-based policy improvement against a convex prior envelope."""
import argparse
from itertools import product
from pathlib import Path
from statistics import mean

import numpy as np

from routing_transfer import HERE, MODES, TOL, a, calibration, digest, frozen, interval, o, wire

MIN_COMPONENT = 0.60
D = interval.D


def vertices(dominant):
    base_laws = o.R.TEST_PRIORS
    base = base_laws[dominant]
    return [base, *(MIN_COMPONENT * base + (1 - MIN_COMPONENT) * other
                    for name, other in base_laws.items() if name != dominant)]


def pick(points, reported, priors, opening, cache):
    grade_values = [float(np.clip(reported + offset, 0, 70)) for offset in (-7, 0, 7)]
    forecasts = [interval.forecasts(calibration(points), grade) for grade in grade_values]
    masses = [o.opening(*opening, prior) for prior in priors]
    catalog, references = {}, {}
    for grade_index, prior_index in product(range(3), range(len(priors))):
        forecast, prior, mass = forecasts[grade_index], priors[prior_index], masses[prior_index]
        key = (grade_values[grade_index], prior_index)
        if key not in cache:
            fixed = {f"fixed_{target}": np.where(D.CHAIR_LEGAL[:, target], target, 0) for target in range(4)}
            policies = {name: (query, o.choose_response(query, mass, forecast)) for name, query in fixed.items()}
            policies["coordinated"], _ = interval.b.improve(forecast, mass, prior, opening)
            grades = {name: o.measure(forecast, mass, prior, opening, policies[name]) for name in fixed}
            cache[key] = (policies, grades["fixed_0"]["released"], max(v["net"] for v in grades.values()))
        candidates, quiet, fixed = cache[key]
        catalog.update({(grade_index, label, prior_index): policy for label, policy in candidates.items()})
        references[grade_index, prior_index] = quiet, fixed

    values = {}
    for key, candidate in catalog.items():
        margins = []
        for (grade, prior), (quiet, fixed) in references.items():
            value = o.measure(forecasts[grade], masses[prior], priors[prior], opening, candidate)
            margins.append((value["released"] - quiet, value["net"] - fixed))
        nominal = o.measure(forecasts[1], masses[0], priors[0], opening, candidate)["net"]
        values[key] = (min(item[0] for item in margins), min(item[1] for item in margins), nominal)
    return {mode: (*interval.select(catalog, values, mode == "interval_fixed"),
                   sum(value[0] >= -TOL for key, value in values.items()
                       if mode == "interval_team" or key[1] != "coordinated"))
            for mode in MODES}, values


def audit():
    routed = wire.n.read(HERE / "routing-results.json")
    assert len(routed["banks"]) == 1 and routed["banks"][0]["arms"] == ["authored", "model"]
    points = np.array(routed["banks"][0]["points"], dtype=float)
    inputs = wire.n.read(HERE / "source-policies.json")["contexts"]
    unique = {}
    for row in routed["rows"]:
        context = row["context"]
        _, label, info = context.split("/")
        opening = tuple(np.array(v) for v in inputs[context]["opening"])
        key = (label, info, tuple(tuple(v) for v in opening), row["review_offset"])
        if key not in unique:
            unique[key] = []
        unique[key].append(row)
    results = []
    caches = {}
    for (label, info, table, offset), source_rows in unique.items():
        actual, _ = a.laws()[label]
        opening = tuple(np.array(v) for v in table)
        mass = o.opening(*opening, actual)
        original = source_rows[0]["performance"]
        old = {mode: original[f"target_{mode}"] for mode in MODES}
        assert all(all(row["performance"][f"target_{mode}"] == old[mode] for mode in MODES) for row in source_rows)
        if info == "correct_mixture":
            result = {mode: old[mode] for mode in MODES}
            qualification = {}
        else:
            priors = vertices(label)
            cache = caches.setdefault((label, table), {})
            chosen, values = pick(points, source_rows[0]["reported_target_pair_grade"], priors, opening, cache)
            controls = o.controls(points, mass, actual, opening)
            best_fixed = max(v["net"] for name, v in controls.items() if name != "exact_ask_reply")
            silence = controls["exact_no_request"]["released"]
            result = {}
            for mode, (_, policy, _) in chosen.items():
                score = o.measure(points, mass, actual, opening, policy)
                assert score["net"] <= controls["exact_ask_reply"]["net"] + TOL
                result[mode] = {k: score[k] for k in ("net", "released", "cost", "queries")}
                result[mode].update(net_over_oracle_fixed=score["net"] - best_fixed,
                                    quality_over_silence=score["released"] - silence)
            qualification = {mode: {"selection": choice, "worst_quality_margin": values[choice][0],
                                    "worst_net_margin": values[choice][1], "eligible_candidates": eligible}
                             for mode, (choice, _, eligible) in chosen.items()}
        results.append({"contexts": [row["context"] for row in source_rows], "review_offset": offset,
                        "prior_information": info, "single_prior": old, "prior_envelope": result,
                        "qualification": qualification})
    summary = {}
    for key, group in (("all", results), ("dominant_only", [r for r in results if r["prior_information"] == "dominant_only"])):
        summary[key] = {}
        for mode in ("single_prior", "prior_envelope"):
            pairs = [(r[mode]["interval_team"], r[mode]["interval_fixed"]) for r in group]
            gains = [team["net"] - fixed["net"] for team, fixed in pairs]
            wins, losses = sum(g > TOL for g in gains), sum(g < -TOL for g in gains)
            summary[key][mode] = {"conditions": len(pairs), "wins": wins, "losses": losses,
                                  "ties": len(pairs) - wins - losses, "mean_gain": mean(gains),
                                  "mean_release_vs_silence": mean(team["quality_over_silence"] for team, _ in pairs),
                                  "below_silence": sum(team["quality_over_silence"] < -TOL for team, _ in pairs),
                                  "mean_gain_over_oracle_fixed": mean(team["net_over_oracle_fixed"] for team, _ in pairs)}
    pins = (Path(__file__), HERE / "prior-protocol.md", HERE / "routing-results.json", HERE / "source-policies.json")
    return {"summary": summary, "rows": results, "sha256": {path.name: digest(path) for path in pins}}


if __name__ == "__main__":
    frozen.emit(audit())
