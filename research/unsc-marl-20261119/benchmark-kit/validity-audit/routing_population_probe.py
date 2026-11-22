"""Test a receipt-only selector with multiple priors and held-out shifts."""
import argparse
import json
from math import factorial
from pathlib import Path

import numpy as np

import routing_active_receipt_probe as active

ident, base, route, robust, pilot = active.ident, active.base, active.route, active.robust, active.pilot
HORIZON = active.PROBES + active.FUTURE
COUNTS = np.array(list(active.compositions(active.PROBES, 7)))
FACTORIAL = np.array([factorial(i) for i in range(active.PROBES + 1)])
MULTINOMIAL = factorial(active.PROBES) / FACTORIAL[COUNTS].prod(axis=1)


def histogram_law(kernel, priors):
    probabilities = priors @ kernel.reshape(8, 64).T
    assert np.allclose(probabilities[:, 7], 0)
    return np.stack([
        active.observation_law(COUNTS, row[:7], MULTINOMIAL) for row in probabilities
    ])


def candidate_tables(pool):
    names, kernels, policies, swaps = [], [], [], []
    for name, policy in pool.items():
        forward = ident.receipt_kernel(policy)
        for swap in (False, True):
            names.append(f"{'swapped' if swap else 'forward'}:{name}")
            kernels.append(forward.transpose(0, 2, 1) if swap else forward)
            policies.append(policy)
            swaps.append(swap)
    return names, kernels, policies, swaps


def values(policies, swaps, points, priors):
    pay = route.receipt_matrix(points, route.TRAIN_LOSS)
    cells = [pilot.cell_returns(policy, pay) for policy in policies]
    flat = np.stack([(cell.T if swap else cell).ravel() for cell, swap in zip(cells, swaps, strict=True)])
    return priors @ flat.T


def plan(kernels, anchor_returns, anchors):
    average = anchor_returns.mean(axis=0)
    fallback = int(average.argmax())
    fixed_total = float(HORIZON * average[fallback])
    best = None
    for idx, kernel in enumerate(kernels):
        # Each hypothesis has equal mass and remains fixed across all episodes.
        joint = histogram_law(kernel, anchors) / len(anchors)
        outcomes = joint.T @ anchor_returns
        decisions = outcomes.argmax(axis=1)
        decisions[joint.sum(axis=0) == 0] = fallback
        total = active.PROBES * average[idx] + active.FUTURE * outcomes.max(axis=1).sum()
        if best is None or total > best[0]:
            best = (float(total), idx, decisions)
    return fixed_total, fallback, best


def evaluate(realized, distributions, kernel, fallback, probe, decisions):
    rows = []
    for rewards, law in zip(realized, histogram_law(kernel, distributions), strict=True):
        fixed = float(HORIZON * rewards[fallback])
        probe_gap = float(active.PROBES * (rewards[probe] - rewards[fallback]))
        future_gap = float(active.FUTURE * (law @ (rewards[decisions] - rewards[fallback])))
        candidate_total = fixed + probe_gap + future_gap
        oracle = float(HORIZON * rewards.max())
        assert max(candidate_total, fixed) <= oracle + 1e-8
        rows.append({
            "fixed_total": fixed,
            "best_candidate_with_prior_total": oracle,
            "probe_phase_gain": probe_gap,
            "future_phase_gain": future_gap,
            "unconditional_probe_gain": probe_gap + future_gap,
            "probability_switch": float(law @ (decisions != fallback)),
            "probability_switch_to_worse_policy": float(law @ (rewards[decisions] < rewards[fallback] - 1e-9)),
        })
    return rows


def run(archive_path, witness_path):
    archive = json.loads(archive_path.read_text())
    witness = json.loads(witness_path.read_text())
    digest = base.space.runner.digest
    assert witness["input_sha256"][archive_path.name] == digest(archive_path)
    anchors = np.array(list(archive["prior_anchors"].values())).reshape(-1, 64)
    anchor_names = list(archive["prior_anchors"])
    assert len(anchors) == 3 and np.allclose(anchors.sum(axis=1), 1)
    cases = {}
    for name, checksum, intended, actual in base.held_out():
        row = archive["historical"][name]
        aliases = witness["historical"][name]
        assert checksum == row["source_sha256"] == aliases["source_sha256"]
        pool = {key: base.space.as_policy(p) for key, p in row["pool"].items()}
        names, kernels, policies, swaps = candidate_tables(pool)
        public = values(policies, swaps, intended, anchors)
        fixed, fallback, (planned, probe, decisions) = plan(kernels, public, anchors)
        replay = evaluate(public, anchors, kernels[probe], fallback, probe, decisions)
        assert np.isclose(planned - fixed, np.mean([x["unconditional_probe_gain"] for x in replay]), atol=1e-10)
        deploy = planned > fixed + 1e-9

        evaluation = {
            **archive["prior_anchors"], **archive["prior_stress"],
            "passive_alias_a": aliases["prior_a"], "passive_alias_b": aliases["prior_b"],
        }
        distributions = np.array(list(evaluation.values())).reshape(-1, 64)
        assert np.all(distributions >= 0) and np.allclose(distributions.sum(axis=1), 1)
        realized = values(policies, swaps, actual, distributions)
        scores = dict(zip(evaluation, evaluate(realized, distributions, kernels[probe], fallback, probe, decisions),
                          strict=True))
        for label, score in scores.items():
            score["gain_from_selected_plan"] = score["unconditional_probe_gain"] if deploy else 0.
            score["split"] = ("anchor" if label in anchor_names else
                              "stress" if label in archive["prior_stress"] else "passive_alias")
        cases[name] = {
            "source_sha256": checksum,
            "fixed_arm": names[fallback], "best_probe_arm": names[probe], "probe_deployed": deploy,
            "planned_gain": planned - fixed, "scores": scores,
        }
    return {
        "scope": "Plan with the intended rubric and three equally likely public anchor inventory distributions. "
                 "Score on the observed record bank under each anchor, four unseen stress distributions, "
                 "and two bank-specific aliases absent from planning. No inventory disclosures or new text generation.",
        "pilot_episodes": active.PROBES, "future_episodes": active.FUTURE, "histograms": len(COUNTS),
        "input_sha256": {path.name: digest(path) for path in (archive_path, witness_path)},
        "scorer_sha256": digest(Path(__file__)),
        "cases": cases,
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--anchor", type=Path, default=robust.OUT / "report.json")
    cli.add_argument("--witness", type=Path, default=robust.OUT / "receipt-identifiability.json")
    args = cli.parse_args()
    print(json.dumps(run(args.anchor, args.witness), indent=2))
