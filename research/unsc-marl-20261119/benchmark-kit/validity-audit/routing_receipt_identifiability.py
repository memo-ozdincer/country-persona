"""Find different priors that one fixed routing protocol logs identically."""
import argparse
import json
from pathlib import Path

import numpy as np

import routing_pilot_recency as recency

d = recency.drift
robust, base, route, pilot = d.robust, d.base, d.route, d.pilot


def receipt_kernel(policy):
    """Columns are private inventory pairs, rows are public receipt masks."""
    ask, send, reply = policy
    n = len(route.STATES)
    kernel = np.zeros((n, n, n))
    loss = route.TRAIN_LOSS
    for left in route.STATES:
        for right in route.STATES:
            first = route.BITS[send[left]]
            for received, p in ((ask[left], 1 - loss), (0, loss)):
                second = route.BITS[reply[right, received]]
                for a, u in ((first, 1 - loss), (0, loss)):
                    for b, v in ((second, 1 - loss), (0, loss)):
                        kernel[a | b, left, right] += p * u * v
    assert np.allclose(kernel.sum(axis=0), 1)
    return kernel


def logging_kernel(policies, selection):
    """Observe the public policy draw, desk orientation, and final receipt only."""
    rows = []
    for key, weight in selection.items():
        forward = .5 * weight * receipt_kernel(policies[key])
        rows.extend((forward, forward.transpose(0, 2, 1)))
    observed = np.concatenate(rows, axis=0).reshape(-1, 64)
    assert np.allclose(observed.sum(axis=0), 1)
    return observed


def ambiguous_pair(channel, candidates, intended):
    matrix = route.receipt_matrix(intended, route.TRAIN_LOSS)
    uniform = route.TEST_PRIORS["uniform"]
    optimum, _ = route.exact_optional(uniform, matrix, route.TRAIN_LOSS)
    best = (-1., None, None)
    for key, policy in {**candidates, "uniform_exact_query": optimum}.items():
        gains = pilot.cell_returns(policy, matrix)
        signal = (gains - gains.T).ravel()
        coeff = np.linalg.lstsq(channel.T, signal, rcond=None)[0]
        diff = (signal - channel.T @ coeff).reshape(8, 8)
        diff = (diff - diff.T) / 2
        if np.max(np.abs(diff)) <= 1e-10:
            continue
        direction = (.8 / 64) * diff / np.max(np.abs(diff))
        separation = float(direction.ravel() @ signal)
        if separation > best[0]:
            best = (separation, key, direction)
    gain, witness, direction = best
    assert gain > 0 and direction is not None
    first, second = uniform + direction, uniform - direction
    assert np.all(first > 0) and np.all(second > 0) and np.allclose(first.T, second)
    assert np.isclose(first.sum(), 1) and np.isclose(second.sum(), 1)
    assert np.max(np.abs(channel @ first.ravel() - channel @ second.ravel())) < 1e-10
    return first, second, witness, gain


def exact_value(reward, prior):
    matrix = route.receipt_matrix(reward, route.TRAIN_LOSS)
    policy, count = route.exact_optional(prior, matrix, route.TRAIN_LOSS)
    return robust.portfolio.contrasts.measure(policy, reward, prior)["net"], count


def run(path, symmetry):
    priors = json.loads(path.read_text())
    public = json.loads(symmetry.read_text())
    assert public["prior_report_sha256"] == base.space.runner.digest(path)
    anchors = {key: np.asarray(p) for key, p in priors["prior_anchors"].items()}
    result = {}
    for name, checksum, intended, actual in base.held_out():
        selected = public["historical"][name]
        reference = priors["historical"][name]
        assert checksum == selected["source_sha256"] == reference["source_sha256"]
        pool = {key: base.space.as_policy(rows) for key, rows in reference["pool"].items()}
        for key, prior in anchors.items():
            if f"sym_independent_{key}" in selected["selection"]:
                matrix = route.receipt_matrix(intended, route.TRAIN_LOSS)
                pool[f"sym_independent_{key}"] = route.best_silent((prior + prior.T) / 2, matrix)
        kernel = logging_kernel(pool, selected["selection"])
        first, second, witness, separation = ambiguous_pair(kernel, pool, intended)
        heldout = {}
        for tag, reward in (("public_rubric", intended), ("observed_record", actual)):
            v1, count = exact_value(reward, first)
            v2, _ = exact_value(reward, second)
            blind, _ = exact_value(reward, (first + second) / 2)
            # A public supervisor who knows which source generated the historic logs can
            # choose the better desk orientation. A receiver of the logs alone cannot.
            known = max(v1, v2)
            assert known >= blind - 1e-9
            heldout[tag] = {"known_prior_and_best_orientation": known, "best_average_without_prior": blind,
                            "blind_average_regret": known - blind, "request_maps_per_solve": count,
                            "query_ceiling_each_fixed_orientation": [v1, v2]}
        observation = kernel @ first.ravel()
        assert np.isclose(observation.sum(), 1)
        result[name] = {"prior_a": first.tolist(), "prior_b": second.tolist(), "logging_policy": selected["selection"],
                        "channel_rank": int(np.linalg.matrix_rank(kernel)),
                        "public_observation_probabilities": observation.tolist(),
                        "max_observational_difference": float(np.max(np.abs(observation - kernel @ second.ravel()))),
                        "witness_policy": witness, "planned_orientation_separation": separation,
                        "scores": heldout, "source_sha256": checksum}
    return {"scope": "Construct two synthetic inventory distributions using only intended reward and a fixed "
                     "symmetric incumbent's logging channel. The logger exposes the policy draw, orientation and "
                     "receipt mask. Each passive pilot has identical likelihood under either distribution. "
                     "The lower bound is mean regret under equal prior weights versus an oracle with known "
                     "prior and requester choice. Adaptive probe policies or richer logs are separate.",
            "input_sha256": {p.name: base.space.runner.digest(p) for p in (path, symmetry)},
            "scorer_sha256": base.space.runner.digest(Path(__file__)), "historical": result}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--input", type=Path, default=robust.OUT / "report.json")
    cli.add_argument("--symmetry", type=Path, default=robust.OUT / "symmetry.json")
    args = cli.parse_args()
    print(json.dumps(run(args.input, args.symmetry), indent=2))
