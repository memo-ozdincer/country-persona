"""Fit a single role-aware joint policy on the written-vote task."""
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import roster_shift as shift
import adaptive_fit as optimizer

relay = shift.relay
HERE = Path(__file__).resolve().parent


def batches():
    """Reuse the exact trajectory compiler, then pool shared responder states."""
    global_states = {}
    all_paths = []
    all_outcomes = []
    all_mass = []
    scenarios = relay.SCENARIOS
    width = 0
    for target, anchor in scenarios:
        prior = shift.distribution(set(target) - {anchor}, shift.TRAIN_STRENGTH, 0)
        with patch.multiple(relay, SCENARIOS=((target, anchor),), DESIGN=prior):
            states, actions, outcomes, mass = optimizer.build()
        count = sum(size for _, size in states.values())
        indices = np.zeros(count + 1, dtype=np.int32)
        indices[-1] = -1
        for state, (offset, size) in states.items():
            if state not in global_states:
                global_states[state] = width, size
                width += size
            target_offset, global_size = global_states[state]
            assert size == global_size
            indices[offset:offset + size] = np.arange(target_offset, target_offset + size)
        all_paths.append(indices[actions])
        all_outcomes.append(outcomes)
        all_mass.append(mass["design_mixture"] / len(scenarios))

    max_width = max(x.shape[1] for x in all_paths)
    actions = np.concatenate([np.pad(x, ((0, 0), (0, max_width - x.shape[1])), constant_values=-1)
                              for x in all_paths])
    return global_states, actions, np.concatenate(all_outcomes), {"design_mixture": np.concatenate(all_mass)}


def outer_run():
    states, paths, outcomes, masses = batches()
    history, fit = optimizer.fit(states, paths, outcomes, masses)
    trained = {state: fit["joint_learned"][start:start + width].tolist() for state, (start, width) in states.items()}
    original = shift.actor_policy()
    assert original.keys() == trained.keys()
    observed = []
    for target, anchor in relay.SCENARIOS:
        roster = shift.distribution(set(target) - {anchor}, shift.TRAIN_STRENGTH, 0)
        cases = {name: shift.transfer.outcomes(policy, target, anchor, roster) for name, policy in (
            ("old", original), ("new", trained))}
        observed.append(shift.score(relay.KEYS, shift.transfer.ftf_bank(), target, anchor, roster, cases))
    on_train = shift.transfer.mean(observed)
    replay = optimizer.evaluate(fit["joint_learned"], paths, outcomes, masses)["design_mixture"]
    assert abs(replay["record_reward"] - history[-1]["record_reward"]) < 1e-9
    for field in ("completion", "cost", "attempts", "final_record_score"):
        assert abs(on_train["new"][field] - replay[field]) < 1e-9
    replay_shift = shift.evaluate({
        "trained_joint": (trained, False),
        "trained_requester_canonical_reply": (trained, True),
    })
    return {"scope": "One exact finite-horizon policy-gradient fit on the original written-vote texts, "
                     "with scenario-specific specialist roster priors. The three target dockets "
                     "and their alternate roster priors do not enter training.",
            "conditions": shift.CONDITIONS, "trained_strength": shift.TRAIN_STRENGTH,
            "update_count": optimizer.STEPS, "unique_local_states": len(states), "trajectory_count": len(paths),
            "training": history, "trained_record": on_train, "transfer": replay_shift,
            "policy": [{"local_state": state, "probabilities": probability} for state, probability in trained.items()],
            "parents": {x.name: shift.runner.digest(x) for x in (
                 Path(optimizer.__file__), Path(shift.__file__), shift.transfer.FROZEN, HERE / "roster-shift-results.json")}}


if __name__ == "__main__":
    print(json.dumps(outer_run(), indent=2))
