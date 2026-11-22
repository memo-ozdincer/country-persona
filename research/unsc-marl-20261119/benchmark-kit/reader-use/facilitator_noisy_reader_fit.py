"""Fit coordinated routing on synthetic relation errors, then replay real briefs."""
from collections import defaultdict
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

import facilitator_receipt_ceiling as ceiling
import facilitator_optional_feedback as channel

base = ceiling.base
HERE = ceiling.HERE
REFERENCE = HERE / "facilitator-receipt-ceiling-results.json"
ERROR = 0.15


def probability(truth, observed):
    return (1 - ERROR) if truth == observed else ERROR / (len(base.RELATIONS) - 1)


def worlds():
    for truth, _, weight in channel.synthetic():
        for observed in product(base.RELATIONS, repeat=2):
            mass = weight * probability(truth[0], observed[0]) * probability(truth[1], observed[1])
            yield truth, observed, mass


def target(truth, reads, receipt):
    return base.utility(base.decision(reads, receipt), base.decision(truth, receipt))


def batch():
    states, _, _, _ = base.trajectories()
    rows = defaultdict(float)
    for truth, reads, mixture in worlds():
        for (left, right), mass in base.base.roster("training").items():
            start_a, _ = states["first", base.local(left, reads)]
            for a, first in enumerate((*left, base.PASS)):
                for ok, ack, reached in base.events(first):
                    observed = base.observation(first, reads, ack)
                    start_b, _ = states["second", base.local(right, reads, observed)]
                    for b, second in enumerate((*right, base.PASS)):
                        value = 0.
                        for arrived, p in ((True, base.base.CHAIR), (False, 1 - base.base.CHAIR)):
                            receipt = base.delivered(first, ok, second, arrived)
                            value += p * target(truth, reads, receipt)
                        rows[start_a + a, start_b + b, base.paid(first, second), value] += mixture * mass * reached
    paths = np.array([(a, b) for a, b, _, _ in rows], dtype=int)
    rewards = np.array([(fee, 0., 35 + value, 0.) for _, _, fee, value in rows])
    return states, paths, rewards, {"design_mixture": np.array(list(rows.values()))}


def expected(weights):
    value = 0.
    for truth, reads, mass in worlds():
        stats, receipts = base.distribution("learned", weights, base.base.roster("training"), truth, reads)
        value += mass * (sum(p * target(truth, reads, seen) for seen, p in receipts.items()) - stats["cost"])
    return value


def run():
    states, paths, rewards, mass = batch()
    opt = base.base.optimizer
    trace, result = opt.fit(states, paths, rewards, mass)
    learned = base.base.observed_weights(states, result["joint_learned"])
    attained = expected(learned)
    assert abs(attained - trace[-1]["record_reward"]) < 1e-9
    frozen, independent = ceiling.stock()
    reference = ceiling.DEV.load(REFERENCE)["evidence"]
    policies = (("noise_trained", "learned", learned), ("noise_trained_erased", "learned_erased", learned),
                ("frozen_adaptive", "learned", frozen), ("trained_independent", "learned_erased", independent),
                ("greedy", "greedy", {}))
    tested = {}
    for scope, cases in ceiling.datasets().items():
        tested[scope] = {}
        for roster in ("split", "overlap"):
            evaluated = ceiling.measure(cases, policies, roster)
            assert all(evaluated[method] == reference[scope][roster]["results"][method]
                       for method in ("frozen_adaptive", "trained_independent", "greedy"))
            assert evaluated["noise_trained"]["summary"][ceiling.MODE]["brief_net"] <= (
                reference[scope][roster]["ceiling"]["opt_adaptive"]["exact_net"] + 1e-9)
            tested[scope][roster] = evaluated
    return {"scope": "One joint fit on synthetic truth and independently corrupted local readings. "
                     "Neither the official case cards nor the reviewed briefs enter the optimizer. "
                     "Noise is a symmetric design assumption. Real readers and language output remain fixed in replay.",
            "local_error_probability": ERROR, "updates": opt.STEPS, "training_trace": trace,
            "synthetic_noisy_net": {"noise_trained": attained, "frozen_adaptive": expected(frozen)},
            "policy": [{"state": state, "probabilities": p} for state, p in learned.items()],
            "replay": tested,
            "inputs_sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in
                              (Path(__file__), Path(ceiling.__file__), REFERENCE, Path(channel.__file__))}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
