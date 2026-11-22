"""Freeze a prior-blind Outer Space policy on its announced rubric and score it."""
import argparse
import json
from pathlib import Path

import numpy as np

import routing_blind_limit as limit

base, route, digest = limit.base, limit.route, limit.digest
CASE = "outer_space"
FIT = limit.FIT_BANK
BOUND = FIT.parent / "blind-limit.json"
FAIR = FIT.parent / "fair-control.json"


def read(path):
    return json.loads(path.read_text())


def selection_inputs():
    archive = read(limit.PRIOR_BANK)
    priors = {name: np.asarray(p) for group in ("prior_anchors", "prior_stress") for name, p in archive[group].items()}
    pool = archive["historical"][CASE]["pool"]
    trained = read(FIT)["historical_replay"][CASE]["policies"]
    return priors, pool, trained


def hashes():
    paths = (Path(__file__), Path(limit.__file__), limit.PRIOR_BANK, FIT, base.space.TASK)
    return {path.name: digest(path) for path in paths}


def plan(anchors_only=False):
    priors, pool, trained = selection_inputs()
    if anchors_only:
        priors = {name: priors[name] for name in route.TEST_PRIORS}
    announced = route.points(base.space.intended())
    table = route.receipt_matrix(announced, route.TRAIN_LOSS)
    controls, results = {}, {}
    for name, prior in priors.items():
        silent = route.best_silent(prior, table)
        controls[name] = [part.tolist() for part in silent]
        results[name] = {"independent": route.evaluate(silent, prior, announced, route.TRAIN_LOSS)["net"]}
    selected = limit.solve({"pool": pool, "results": results}, {"policies": trained}, announced, priors)

    # An implementable independent baseline uses the same public planning information.
    average = np.mean(list(priors.values()), axis=0)
    controls["average"] = [part.tolist() for part in route.best_silent(average, table)]
    values = np.array([
        [route.evaluate(base.space.as_policy(p), q, announced, route.TRAIN_LOSS)["net"] for p in controls.values()]
        for q in priors.values()
    ])
    _, independent_weights = limit.game_search(values - np.array([row["independent"] for row in results.values()])[:, None])
    return {
        "scope": "Outer Space is an exposed docket selected after a positive retrospective feasibility finding. "
                 "This planning step passes only the advertised rubric and public policy inputs to optimization. "
                 "The current prior identity is hidden. The listed priors are the only ones used for planning.",
        "input_hashes": hashes(), "announced_points": announced.tolist(), "priors": list(priors),
        "optimized_independence_announced": results, "planned_team": selected,
        "independent_tables": controls,
        "planned_independent_mixture": dict(zip(controls, independent_weights.tolist(), strict=True)),
    }


def score(plan_path):
    planned = read(plan_path)
    assert planned["input_hashes"] == hashes()
    priors, pool, trained = selection_inputs()
    _, checksum, announced, observed = next(row for row in base.held_out() if row[0] == CASE)
    np.testing.assert_array_equal(announced, planned["announced_points"])
    oracle = read(limit.PRIOR_BANK)["historical"][CASE]
    assert checksum == oracle["source_sha256"]
    team = planned["planned_team"]
    seeds = {**pool, **trained}
    strategies = {}
    for label, weight in team["feasible_mixture"]["mixture"].items():
        if label in team["added_policies"]:
            policy = team["added_policies"][label]["policy"]
            swapped = team["added_policies"][label]["swap_desks"]
        else:
            orientation, name = label.split(":", 1)
            swapped, policy = orientation == "swapped", seeds[name]
        strategies[label] = (base.space.as_policy(policy), swapped, weight)
    silent = {
        name: (base.space.as_policy(p), planned["planned_independent_mixture"][name])
        for name, p in planned["independent_tables"].items()
    }
    assert np.isclose(sum(weight for _, _, weight in strategies.values()), 1)
    assert np.isclose(sum(weight for _, weight in silent.values()), 1)
    outcomes = {}
    public_table = route.receipt_matrix(announced, route.TRAIN_LOSS)
    for name, prior in priors.items():
        result = oracle["results"][name]
        ref = result["independent"]
        own_reference = route.evaluate(route.best_silent(prior, public_table), prior, announced,
                                        route.TRAIN_LOSS)["net"]
        planned_value = sum(weight * route.evaluate(policy, prior.T if swapped else prior, announced,
                                                       route.TRAIN_LOSS)["net"]
                            for policy, swapped, weight in strategies.values())
        if name in planned["priors"]:
            assert abs(planned_value - own_reference - team["feasible_mixture"]["gain_by_prior"][name]) < 1e-8
        actual_value = sum(weight * route.evaluate(policy, prior.T if swapped else prior, observed,
                                                       route.TRAIN_LOSS)["net"]
                           for policy, swapped, weight in strategies.values())
        actual_erased = sum(weight * route.evaluate(policy, prior.T if swapped else prior, observed,
                                                        route.TRAIN_LOSS, force_missing=True)["net"]
                            for policy, swapped, weight in strategies.values())
        silent_value = sum(weight * route.evaluate(policy, prior, observed, route.TRAIN_LOSS)["net"]
                           for policy, weight in silent.values())
        assert silent_value <= ref + 1e-8
        outcomes[name] = {"used_in_planning": name in planned["priors"],
                          "announced_gain": planned_value - own_reference, "actual_team_net": actual_value,
                          "actual_independent_net": silent_value, "prior_informed_independence": ref,
                          "actual_gain_vs_informed_independence": actual_value - ref,
                          "actual_gain_vs_same_information_plan": actual_value - silent_value,
                          "question_erasure_drop": actual_value - actual_erased}
    fair = read(FAIR)
    assert fair["blind_limit_sha256"] == digest(BOUND)
    hindsight = read(BOUND)["cases"][CASE]
    lower = min(row["actual_gain_vs_informed_independence"] for row in outcomes.values())
    independent_upper = fair["cases"][CASE]["worst_case_independence_upper"]
    return {
        "planning_artifact_sha256": digest(plan_path), "scored_bank_sha256": checksum,
        "announced_points": announced.tolist(), "realized_points": observed.tolist(),
        "actual_worst_case_gain": lower, "hindsight_feasible_worst_gain": hindsight["worst_gain_lower"],
        "hindsight_upper": hindsight["worst_gain_upper"],
        "certified_advantage_over_optimal_prior_blind_independence": lower - independent_upper,
        "outcomes": outcomes,
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("plan", "score"))
    cli.add_argument("path", type=Path, nargs="?")
    cli.add_argument("--anchors-only", action="store_true")
    args = cli.parse_args()
    result = plan(args.anchors_only) if args.mode == "plan" else score(args.path)
    print(json.dumps(result, indent=2))
