"""Match publication, correction and withholding frequencies in the training mixture."""
from collections import Counter
from itertools import product
from hashlib import sha256
import json
from pathlib import Path

import facilitator_policy as base
from facilitator_policy_audit import freeze

HERE = base.HERE
PARENT = HERE / "facilitator-policy.json"


def run():
    truth = tuple(product(base.RELATIONS, repeat=2))
    category = {status: base.decision(status, base.TARGETS) for status in truth}
    counts = Counter(category.values())
    weights = {status: 1 / (len(counts) * counts[acted]) for status, acted in category.items()}
    assert abs(sum(weights.values()) - 1) < 1e-9
    states, paths, outcomes, exogenous = base.trajectories(weights)
    trace, strategy = base.base.optimizer.fit(states, paths, outcomes, exogenous)
    learned = base.base.observed_weights(states, strategy["joint_learned"])
    prior_fit = base.endpoint.delivery.load(PARENT)
    old = {freeze(info["state"]): info["probabilities"] for info in prior_fit["policy"]}
    assert old.keys() == learned.keys()
    training = {}
    for name in ("learned", "learned_erased", "old_fit", "greedy", "greedy_erased"):
        policy, variant = (old, "learned") if name == "old_fit" else (learned, name)
        rows = {status: base.distribution(variant, policy, base.base.roster("training"), status, status)[0] for status in truth}
        training[name] = {key: sum(rows[status][key]*weights[status] for status in truth)
                          for key in next(iter(rows.values()))}
    assert abs(training["learned"]["net"] - trace[-1]["record_reward"]) < 1e-9
    evaluation = base.replay(learned)
    for regime, record in evaluation.items():
        earlier = prior_fit["replay"][regime]
        assert record["greedy"] == earlier["greedy"]
        assert record["greedy_erased"] == earlier["greedy_erased"]
        record.update({"uniform_fit": earlier["learned"], "uniform_fit_erased": earlier["learned_erased"]})
    return {"scope": "One exact matched fit on synthetic relations with equal mass on the three disposition classes. "
                     "Class labels change sampling weights, but the actors see only their own source states and receipts. "
                     "Existing writer and citation reviews are replayed unchanged.",
            "inputs": {str(p.relative_to(HERE)): sha256(p.read_bytes()).hexdigest()
                       for p in (Path(__file__), Path(base.__file__), PARENT, base.CITATIONS,
                                 HERE / "routed-common-ground-evidence/results.json")},
            "weights": [{"relation_pair": status, "mass": weight} for status, weight in weights.items()],
            "updates": base.base.optimizer.STEPS, "training": trace, "training_metrics": training, "replay": evaluation,
            "policy": [{"state": key, "probabilities": prob} for key, prob in learned.items()]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
