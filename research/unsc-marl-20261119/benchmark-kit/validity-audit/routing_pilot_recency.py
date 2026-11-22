"""Use recent predictive returns to decide whether archived pilot data are useful."""
import argparse
import json
from pathlib import Path

import numpy as np

import routing_pilot_drift as drift

robust, base, route, pilot = drift.robust, drift.base, drift.route, drift.pilot


def candidate_scores(planned, actual, old, recent, target, fallback):
    """Cross-validate table selection on recent pilot rows without future scores."""
    old = old.reshape(len(old), 64)
    recent = recent.reshape(len(recent), 64)
    target = target.ravel()
    planned = planned.reshape(len(planned), 64)
    actual = actual.reshape(len(actual), 64)
    uniform = pilot.UNIFORM_MASS * planned.mean(axis=1)
    old_arm = (old @ planned.T + uniform).argmax(axis=1)
    recent_total = recent @ planned.T + uniform
    recent_arm = recent_total.argmax(axis=1)
    # Each credited prediction comes from a table chosen with that observation removed.
    # Repeated occurrences at one inventory cell have identical leave-one-out rankings.
    chosen_without_cell = (recent_total[:, None, :] - planned.T[None, :, :]).argmax(axis=-1)
    positions = np.arange(64)[None, :]
    leave_one_out = (recent * planned[chosen_without_cell, positions]).sum(axis=1) / drift.RECENT
    old_validation = (recent * planned[old_arm]).sum(axis=1) / drift.RECENT
    fallback_validation = recent @ fallback[0].ravel() / drift.RECENT
    decisions = np.column_stack((fallback_validation, old_validation, leave_one_out)).argmax(axis=1)
    evaluated = actual @ target
    fallback_net = float(fallback[1].ravel() @ target)
    net = np.choose(decisions, [fallback_net, evaluated[old_arm], evaluated[recent_arm]])
    assert len(net) == drift.TRIALS
    return {"chosen": decisions, "net": net, "old": evaluated[old_arm], "recent": evaluated[recent_arm],
            "fallback": fallback_net}


def symmetric_fallback(pool, selection, planned, actual, priors):
    for role in priors:
        key = f"sym_independent_{role}"
        if key in selection:
            p = priors[role]
            pool[key] = route.best_silent((p + p.T) / 2, planned)
    a = 0.
    b = 0.
    for label, weight in selection.items():
        public = pilot.cell_returns(pool[label], planned)
        hidden = pilot.cell_returns(pool[label], actual)
        a += weight * (public + public.T) / 2
        b += weight * (hidden + hidden.T) / 2
    return a, b


def run(priors_path, symmetry_path, drift_path):
    priors = json.loads(priors_path.read_text())
    matching = json.loads(symmetry_path.read_text())
    matched_cost = json.loads(drift_path.read_text())
    assert matched_cost["input_sha256"] == {p.name: base.space.runner.digest(p) for p in (priors_path, symmetry_path)}
    anchors = {k: np.asarray(p) for k, p in priors["prior_anchors"].items()}
    stress = {k: np.asarray(p) for k, p in priors["prior_stress"].items()}
    truth = {**anchors, **stress}
    rng = np.random.default_rng(drift.SEED)
    trials = {tag: drift.pilot_windows(truth[old], truth[new], rng) for tag, (old, new) in drift.TRANSITIONS.items()}
    cases = {}
    for name, checksum, wanted, observed in base.held_out():
        original = priors["historical"][name]
        control = matching["historical"][name]
        assert original["source_sha256"] == control["source_sha256"] == checksum
        matrix = route.receipt_matrix(wanted, route.TRAIN_LOSS)
        actual = route.receipt_matrix(observed, route.TRAIN_LOSS)
        pool = {k: base.space.as_policy(p) for k, p in original["pool"].items()}
        by_policy = [np.stack([pilot.cell_returns(policy, f) for policy in pool.values()]) for f in (matrix, actual)]
        planned_bank, actual_bank = [np.concatenate((arr, arr.transpose(0, 2, 1))) for arr in by_policy]
        fallback = symmetric_fallback(pool, control["selection"], matrix, actual, anchors)
        outcomes = {}
        for label, (_, target) in drift.TRANSITIONS.items():
            old, _ = trials[label]["stale32"]
            recent, _ = trials[label]["fresh8"]
            result = candidate_scores(planned_bank, actual_bank, old, recent, truth[target], fallback)
            symmetric = control["results"][target]["symmetric_routing"]
            assert abs(result["fallback"] - symmetric) < 1e-8
            original_drift = matched_cost["cases"][name][label]["scores"]
            recent_hybrid = original_drift["fresh8"]["versus_symmetric_no_pilot"]
            net = result["net"]
            outcomes[label] = {
                "chosen": dict(zip(("no_pilot_default", "old32", "recent8"),
                                   np.bincount(result["chosen"], minlength=3).tolist(), strict=True)),
                "mean_gain_over_recent_only_library": float((net - result["recent"]).mean()),
                "mean_gain_over_old_only_library": float((net - result["old"]).mean()),
                "mean_gain_over_fresh8_hybrid": float(net.mean() - symmetric -
                                                     recent_hybrid["mean_future_gain_before_collection"]),
                "archived_old_samples": drift.economic(net, symmetric, drift.RECENT),
                "collect_all_samples": drift.economic(net, symmetric, drift.PAST + drift.RECENT),
            }
        cases[name] = outcomes
    return {"scope": "Prior counts remain synthetic. Select the old, recent-only, or prior-agnostic policy by "
                     "predicting expected rubric scores on recent held-out pilot observations. "
                     "No future inventory, realized reward or prior label enters selection. "
                     "Results report both free archival access and collecting the entire pilot.",
            "input_sha256": {p.name: base.space.runner.digest(p) for p in (priors_path, symmetry_path, drift_path)},
            "selector_sha256": base.space.runner.digest(Path(__file__)), "cases": cases}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    home = robust.OUT
    cli.add_argument("--input", type=Path, default=home / "report.json")
    cli.add_argument("--symmetry", type=Path, default=home / "symmetry.json")
    cli.add_argument("--drift", type=Path, default=home / "pilot-drift.json")
    args = cli.parse_args()
    print(json.dumps(run(args.input, args.symmetry, args.drift), indent=2))
