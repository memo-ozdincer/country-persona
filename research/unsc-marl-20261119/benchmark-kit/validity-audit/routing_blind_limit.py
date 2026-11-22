"""Bound worst-prior performance for any prior-blind two-desk strategy."""
import argparse
import json
from pathlib import Path

import numpy as np

import routing_prior_pilot as pilot
import routing_prior_robustness as robust

base, route = robust.base, robust.route
digest = base.space.runner.digest
PRIOR_BANK = robust.OUT / "report.json"
FIT_BANK = base.space.OUT / "routing-regret-training/report.json"
MAX_ROUNDS = 8
TOLERANCE = .003


def game_search(gains):
    """Use averaged multiplicative weights to propose feasible mixtures for both players."""
    rows, columns = gains.shape
    pay = gains / max(np.max(np.abs(gains)), 1.)
    prior_log, policy_log = np.zeros(rows), np.zeros(columns)
    mean_prior, mean_policy = np.zeros(rows), np.zeros(columns)

    def distribution(logits):
        odds = np.exp(logits - logits.max())
        return odds / odds.sum()

    for _ in range(4096):
        prior, policy = distribution(prior_log), distribution(policy_log)
        mean_prior += prior
        mean_policy += policy
        prior_log -= .22 * (pay @ policy)
        policy_log += .22 * (prior @ pay)
    return mean_prior / mean_prior.sum(), mean_policy / mean_policy.sum()


def prices(table, prior, baseline, oriented):
    policy, examined = route.exact_optional(prior.T if oriented else prior, table, route.TRAIN_LOSS)
    returns = pilot.cell_returns(policy, table)
    if oriented:
        returns = returns.T
    return float((returns * prior).sum() - baseline), returns, examined, policy


def solve(archive, fits, actual, priors):
    table = route.receipt_matrix(actual, route.TRAIN_LOSS)
    baseline = np.array([archive["results"][name]["independent"] for name in priors])
    stack = np.stack(list(priors.values()))
    seeds = {**archive["pool"], **fits["policies"]}
    value_cells = []
    policy_labels = []
    for name, p in seeds.items():
        values = pilot.cell_returns(base.space.as_policy(p), table)
        value_cells.extend([values, values.T])
        policy_labels.extend([f"forward:{name}", f"swapped:{name}"])
    gains = np.einsum("klr,glr->gk", np.stack(value_cells), stack) - baseline[:, None]
    trace = []
    best_upper, best_lower = np.inf, -np.inf
    best_certificate, lower_policy = None, None
    added = {}
    for step in range(MAX_ROUNDS):
        p_weights, table_weights = game_search(gains)
        observed_gains = gains @ table_weights
        lower = float(observed_gains.min())
        if lower > best_lower:
            best_lower = lower
            lower_policy = {
                "mixture": {key: float(m) for key, m in zip(policy_labels, table_weights, strict=True) if m > 0},
                "gain_by_prior": dict(zip(priors, map(float, observed_gains), strict=True)),
            }
        mixed = np.einsum("g,glr->lr", p_weights, stack)
        offset = float(baseline @ p_weights)
        states = [prices(table, mixed, offset, swap) for swap in (False, True)]
        winner = max(range(len(states)), key=lambda i: states[i][0])
        upper, cert, count, policy = states[winner]
        assert upper >= float((p_weights @ gains).max()) - 1e-8
        if upper < best_upper:
            best_upper = upper
            best_certificate = {
                "prior_mixture": dict(zip(priors, map(float, p_weights), strict=True)),
                "forward_upper": states[0][0], "swapped_upper": states[1][0], "per_orientation_maps": count,
                "argmax_tables": [[part.tolist() for part in state[3]] for state in states],
            }
        assert best_upper >= best_lower - 1e-8
        trace.append({"round": step + 1, "lower": best_lower, "upper": best_upper})
        if best_upper - best_lower <= TOLERANCE or best_upper < -TOLERANCE or step + 1 == MAX_ROUNDS:
            break
        gains = np.column_stack((gains, np.einsum("lr,glr->g", cert, stack) - baseline))
        label = f"pricing:{step}"
        policy_labels.append(label)
        added[label] = {"policy": [part.tolist() for part in policy], "swap_desks": bool(winner)}
    return {"worst_gain_lower": best_lower, "worst_gain_upper": best_upper,
            "exact_pricing_certificate": best_certificate, "feasible_mixture": lower_policy,
            "added_policies": added, "trace": trace, "target_is_impossible": best_upper < -1e-8}


def run(fit_path):
    archive = json.loads(PRIOR_BANK.read_text())
    fit = json.loads(fit_path.read_text())
    priors = {name: np.asarray(p) for group in ("prior_anchors", "prior_stress") for name, p in archive[group].items()}
    records = {}
    for name, checksum, _, actual in base.held_out():
        original = archive["historical"][name]
        fitted = fit["historical_replay"][name]
        assert checksum == original["source_sha256"] == fitted["source_sha256"]
        records[name] = solve(original, fitted, actual, priors)
    return {
        "scope": "Hindsight limit using the realized archived rubric. Policies do not know which of seven fixed "
                 "inventory priors generated the episode. A public mixture of protocol tables and desk orientations "
                 "is allowed. The independent comparator may know the true prior. The search for dual weights is "
                 "approximate, and every stated upper bound uses exact pricing for both orientations.",
        "source_hashes": {"prior_bank": digest(PRIOR_BANK), "fit_bank": digest(fit_path),
                          "script": digest(Path(__file__))},
        "cases": records,
    }


def verify_report(report_path, fit_path):
    report = json.loads(report_path.read_text())
    archive = json.loads(PRIOR_BANK.read_text())
    fit = json.loads(fit_path.read_text())
    assert report["source_hashes"] == {"prior_bank": digest(PRIOR_BANK), "fit_bank": digest(fit_path),
                                       "script": digest(Path(__file__))}
    priors = {name: np.asarray(p) for group in ("prior_anchors", "prior_stress") for name, p in archive[group].items()}
    restored = {}
    for case, _, _, actual in base.held_out():
        record = report["cases"][case]
        inputs = archive["historical"][case]
        source_tables = {**inputs["pool"], **fit["historical_replay"][case]["policies"]}
        feasible = record["feasible_mixture"]
        assert np.isclose(sum(feasible["mixture"].values()), 1) and min(feasible["mixture"].values()) >= 0
        recomputed = {}
        for name, prior in priors.items():
            score = 0.
            for label, weight in feasible["mixture"].items():
                if label in record["added_policies"]:
                    row = record["added_policies"][label]
                    policy, swapped = row["policy"], row["swap_desks"]
                else:
                    orientation, key = label.split(":", 1)
                    policy, swapped = source_tables[key], orientation == "swapped"
                score += weight * route.evaluate(base.space.as_policy(policy), prior.T if swapped else prior,
                                                 actual, route.TRAIN_LOSS)["net"]
            recomputed[name] = score - inputs["results"][name]["independent"]
            assert abs(recomputed[name] - feasible["gain_by_prior"][name]) < 1e-8
        assert abs(min(recomputed.values()) - record["worst_gain_lower"]) < 1e-8
        cert = record["exact_pricing_certificate"]
        weights = cert["prior_mixture"]
        assert np.isclose(sum(weights.values()), 1) and min(weights.values()) >= 0
        mixture = sum(weight * priors[name] for name, weight in weights.items())
        baseline = sum(weight * inputs["results"][name]["independent"] for name, weight in weights.items())
        table = route.receipt_matrix(actual, route.TRAIN_LOSS)
        bounds = [prices(table, mixture, baseline, swap)[0] for swap in (False, True)]
        assert np.allclose(bounds, [cert["forward_upper"], cert["swapped_upper"]], rtol=0, atol=1e-8)
        assert abs(max(bounds) - record["worst_gain_upper"]) < 1e-8
        restored[case] = {"feasible_worst_gain": min(recomputed.values()), "exact_priced_upper": max(bounds)}
    return {"report_sha256": digest(report_path), "cases": restored}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--fit", type=Path, default=FIT_BANK)
    cli.add_argument("--verify", type=Path)
    args = cli.parse_args()
    result = verify_report(args.verify, args.fit) if args.verify else run(args.fit)
    print(json.dumps(result, indent=2))
