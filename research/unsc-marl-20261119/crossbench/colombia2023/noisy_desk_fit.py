"""Train complete delivery under a balanced mixture of correct and incorrect desk labels."""
import json
from pathlib import Path
from unittest.mock import patch

import full_target_fit as parent

HERE = parent.HERE
roster = parent.roster
relay = parent.relay
optimizer = parent.optimizer
PREVIOUS = HERE / "full-target-fit.json"
DESIGNED_CORRECT = .5
TEST_RELIABILITIES = (0., .25, .5, .75, 1.)


def mixture(pending, strength, labelled, proportion):
    correct = ORIGINAL_DISTRIBUTION(pending, strength, labelled)
    wrong = ORIGINAL_DISTRIBUTION(pending, strength, 1 - labelled)
    return {world: proportion * correct[world] + (1 - proportion) * wrong[world] for world in correct}


def compile_mixed():
    def balanced(pending, strength, label):
        return mixture(pending, strength, label, DESIGNED_CORRECT)

    # Compile the same local trajectories in coordinates where slot A is
    # the desk named by the label. The hidden probability mass changes.
    with patch.object(roster, "distribution", balanced):
        return parent.specialist.batches()


ORIGINAL_DISTRIBUTION = roster.distribution


def read_policy(archive):
    return {roster.transfer.immutable(row["local_state"]): row["probabilities"] for row in archive["policy"]}


def training_replay(states, paths, terminal, masses, policies):
    outcomes = {}
    for label, weights in policies.items():
        assert states.keys() == weights.keys()
        assert all(abs(sum(p) - 1) < 1e-9 and all(0 <= x <= 1 for x in p) for p in weights.values())
        vector = [0.] * (1 + sum(width for _, width in states.values()))
        vector[-1] = 1.
        for state, (offset, width) in states.items():
            vector[offset:offset + width] = weights[state]
        array = optimizer.np.array(vector)
        outcomes[label] = optimizer.evaluate(array, paths, terminal, masses)["design_mixture"]
    return outcomes


def reliability(transfer):
    curves = {}
    for family, outcome in transfer.items():
        correct = outcome["strong_specialist_B"]
        wrong = outcome["mislabelled_specialist_B"]
        strength = roster.CONDITIONS["strong_specialist_B"][0]
        cases = zip(relay.SCENARIOS, correct["scenarios"], strict=True)
        attainable = [(target, anchor, correct_case["upper_bound"]["full_target_release"] > 0)
                      for (target, anchor), correct_case in cases]
        curves[family] = []
        for p in TEST_RELIABILITIES:
            policy_mean = {name: {metric: p * value + (1 - p) * wrong["mean"][name][metric]
                                  for metric, value in scores.items()}
                           for name, scores in correct["mean"].items()}
            oracles = [parent.ceiling.solve(target, anchor,
                                           mixture(set(target) - {anchor}, strength, 1, p), feasible, True)
                       for target, anchor, feasible in attainable]
            oracle = {key: sum(result[key] for result in oracles) / len(oracles)
                      for key in ("full_target_release", "strict_net", "cost")}
            # An unobserved metadata flip also defines a mixture of two physical
            # priors. The mixed-prior oracle cannot tailor actions per latent flip.
            assert oracle["strict_net"] <= (p * correct["oracle"]["strict_net"]
                                             + (1 - p) * wrong["oracle"]["strict_net"]) + 1e-9
            assert all(row["strict_net"] <= oracle["strict_net"] + 1e-9 for row in policy_mean.values())
            curves[family].append({"label_accuracy": p, "observed_policies": policy_mean, "mixed_prior_oracle": oracle})
    return curves


def run():
    states, paths, word_vote, masses = compile_mixed()
    terminal = word_vote.copy()
    terminal[:, 2] = 35 + parent.VALUE * word_vote[:, 1]
    history, fit = optimizer.fit(states, paths, terminal, masses)
    joint = fit["joint_learned"]
    trained = {state: joint[offset:offset + width].tolist() for state, (offset, width) in states.items()}
    raw = read_policy(roster.transfer.read(parent.PARENT))
    clean = read_policy(roster.transfer.read(PREVIOUS))
    common = {"raw_score": raw, "clean_full_delivery": clean, "noisy_full_delivery": trained}
    on_train = training_replay(states, paths, terminal, masses, common)
    assert abs(on_train["noisy_full_delivery"]["record_reward"] - history[-1]["record_reward"]) < 1e-9
    # Preserve the baseline name required by the prior replay's audit.
    policies = {(key if key != "raw_score" else "raw_reward"): (weights, False) for key, weights in common.items()}
    policies["noisy_with_canonical_reply"] = trained, True
    reviewed = parent.replay(policies)
    earlier = roster.transfer.read(PREVIOUS)["transfer"]
    for family, scenarios in reviewed.items():
        for condition, row in scenarios.items():
            assert row["mean"]["clean_full_delivery"] == earlier[family][condition]["mean"]["full_delivery_reward"]
    return {
        "scope": "One fit on written voting with half of the specialist labels correct and half reversed. "
                 "The actors receive the labelled desk order but no event-level indication that it is correct. "
                 "The new policy is replayed without changes in UNIFIL and Colombia.",
        "frozen_inputs": parent.lock() | {p.name: roster.runner.digest(p) for p in (Path(__file__), PREVIOUS)},
        "train_correct_label_probability": DESIGNED_CORRECT, "updates": optimizer.STEPS,
        "training": {"history": history, "metrics": on_train, "trajectories": len(paths), "states": len(states)},
        "transfer": reviewed, "label_reliability": reliability(reviewed),
        "policy": [{"local_state": state, "probabilities": p} for state, p in trained.items()],
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
