"""Verify and diagnose the frozen facilitator fit without training again."""
from collections import defaultdict
from itertools import product
import json

import facilitator_policy as fit

ROOT = fit.HERE / "facilitator-policy.json"


def freeze(obj):
    return tuple(freeze(x) for x in obj) if isinstance(obj, list) else obj


def run():
    stored = fit.endpoint.delivery.load(ROOT)
    policy = {freeze(row["state"]): row["probabilities"] for row in stored["policy"]}
    assert len(policy) == stored["states"]
    states, paths, terminal, mass = fit.trajectories()
    vector = fit.np.ones(1 + sum(width for _, width in states.values()))
    for state, (offset, width) in states.items():
        values = policy[state]
        assert len(values) == width and abs(sum(values) - 1) < 1e-9
        vector[offset:offset + width] = values
    gradient_replay = fit.base.optimizer.evaluate(vector, paths, terminal, mass)["design_mixture"]
    assert abs(gradient_replay["record_reward"] - stored["training"][-1]["record_reward"]) < 1e-9
    assert fit.replay(policy) == stored["replay"]
    truth_patterns = tuple(product(fit.RELATIONS, repeat=2))
    proposal_counts = defaultdict(int)
    group = defaultdict(list)
    for truth in truth_patterns:
        act = fit.decision(truth, fit.TARGETS)
        proposal_counts[act] += 1
        for name in ("learned", "learned_erased", "greedy", "greedy_erased"):
            result, _ = fit.distribution(name, policy, fit.base.roster("training"), truth, truth)
            group[name, act].append(result)
    category_means = {}
    for (policy_name, category), records in group.items():
        category_means.setdefault(policy_name, {})[category] = {k: sum(r[k] for r in records) / len(records)
                                                                for k in records[0]}
    uniform = {name: {metric: sum(category[metric] * proposal_counts[act]/9
                                  for act, category in categories.items())
                      for metric in next(iter(categories.values()))}
               for name, categories in category_means.items()}
    assert abs(uniform["learned"]["net"] - gradient_replay["record_reward"]) < 1e-9
    historical = defaultdict(int)
    for truth, _, _ in fit.cases():
        historical[fit.decision(truth, fit.TARGETS)] += 1
    return {"training_proposal_counts": dict(proposal_counts), "historical_proposal_counts": dict(historical),
            "uniform_training_mean": uniform, "training_means_by_required_disposition": category_means}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
