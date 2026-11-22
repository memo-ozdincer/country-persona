"""Select among jointly learned policies with a receipt-level release constraint."""
from hashlib import sha256
import json
import sys

import numpy as np

from duplicate_card_outcome_policy import (
    EVIDENCE, FIT, PRIORS, PRIVATE, RECEIPT, SIGNAL_COST, TESTS, TRAIN, TRAIN_PROFILES,
    archived_profiles, exact, fit_repertoire, net_matrix, play, rollout,
)

FIRST_RUN = EVIDENCE / "outcome-policy.json"
GUARDED_PROFILE = {"guarded_pair": (0, -70, -70, 7)}


def fit_joint_phases():
    rewards = np.asarray(GUARDED_PROFILE["guarded_pair"])[RECEIPT]
    matrix = net_matrix(rewards)
    trained_return, signals, actions = exact(TRAIN, matrix, SIGNAL_COST)["optional"]
    table = np.full((2, 4, 5), -1, dtype=np.int8)
    for private, bits, delivery in zip(PRIVATE, signals, actions, strict=True):
        for seat in (0, 1):
            own, peer = bits[seat], bits[1 - seat]
            position = 1 + 2 * own + peer
            row = table[seat, private[seat]]
            assert row[0] in (-1, own) and row[position] in (-1, delivery[seat])
            row[0], row[position] = own, delivery[seat]
    # Unvisited entries are unreachable with these announcement policies.
    table[table == -1] = 0
    replay_bits, replay_actions, returns = play(table[None], matrix)
    assert np.array_equal(replay_bits[0], signals) and np.array_equal(replay_actions[0], actions)
    assert np.isclose(returns[0] @ TRAIN, trained_return)
    return table[None], [[{"expected_training_return": trained_return}]]


def run(warm=False, phase=False):
    original = json.loads(FIRST_RUN.read_text())
    old_tables = np.asarray(original["training"]["tables"])
    initial = old_tables[[list(TRAIN_PROFILES).index("both_or_neither")]] if warm else None
    guarded_tables, history = fit_joint_phases() if phase else fit_repertoire(GUARDED_PROFILE, initial)
    matrices, sources = archived_profiles()
    assert original["score_artifact_sha256"] == sources
    assert original["frozen_proof_policy_sha256"] == sha256(FIT.read_bytes()).hexdigest()
    proof_table = np.asarray(json.loads(FIT.read_text())["learned_table"])
    tables = np.concatenate([old_tables, guarded_tables, proof_table[None]], axis=0)
    extra = "joint_phase_fit" if phase else next(iter(GUARDED_PROFILE))
    names = [*TRAIN_PROFILES, extra, "frozen_proof_router"]
    result = {}
    for test, (proxy_key, truth_key) in TESTS.items():
        proxy = matrices[proxy_key]
        truth = matrices[truth_key]
        estimated = net_matrix(proxy)
        bits, actions, _ = play(tables, estimated)
        _, silent_bits, silent_actions = exact(TRAIN, estimated, SIGNAL_COST)["silent"]
        schemes = {
            **dict(zip(names, zip(bits, actions, strict=True), strict=True)),
            "calibrated_silent": (silent_bits, silent_actions),
            "withhold_all": (np.zeros_like(silent_bits), np.zeros_like(silent_actions)),
        }
        # Applied only when the calibrated endpoint defines a rejected record as
        # zero and has an eligible empty fallback. All 16 possible inventories
        # are checked, including ones with lower probability under calibration.
        enforce = proxy_key.endswith("_release") and bool(proxy[0, 0] > 0)
        eligible = {}
        rejected = []
        for name, (signal, delivery) in schemes.items():
            if enforce and np.any(proxy[tuple(delivery.T)] == 0):
                rejected.append(name)
            else:
                eligible[name] = rollout(TRAIN, proxy, signal, delivery)["net"]
        selected = max(eligible, key=eligible.get)
        result[test] = {"selected": selected, "enforced": enforce, "ineligible_strategies": rejected,
                        "eligible_calibration_net": eligible, "priors": {}}
        for prior_name, prior in PRIORS.items():
            actual = rollout(prior, truth, *schemes[selected])
            exact_upper = exact(prior, net_matrix(truth), SIGNAL_COST)["optional"][0]
            assert actual["net"] <= exact_upper + 1e-9
            if truth_key.endswith("_release"):
                rejected_worlds = truth[tuple(schemes[selected][1].T)] == 0
                actual["rejected_record_probability"] = float(prior @ rejected_worlds)
            previous = original["evaluation"][test]["priors"][prior_name]
            result[test]["priors"][prior_name] = {
                "guarded": actual,
                "first_run_net": previous["outcome_repertoire"]["net"],
                "calibrated_silent_net": previous["calibrated_silent"]["net"],
                "frozen_proof_router_net": previous["frozen_proof_router"]["net"],
                "exact_optional_net": exact_upper,
            }
            if (warm or phase) and truth_key.endswith("_release"):
                # Every inventory has at least 1% mass. This penalty rules out
                # forbidden receipts because the approved values are at most 70.
                assert prior.min() >= .01 - 1e-9 and truth.max() <= 70
                eligible_matrix = np.where(truth == 0, -10_000, net_matrix(truth))
                safe = exact(prior, eligible_matrix, SIGNAL_COST)["optional"]
                assert not np.any(truth[tuple(safe[2].T)] == 0)
                result[test]["priors"][prior_name]["exact_eligible_optional_net"] = safe[0]
    report = {"first_run_sha256": sha256(FIRST_RUN.read_bytes()).hexdigest(),
            "guarded_synthetic_profile": GUARDED_PROFILE,
            "guarded_table": guarded_tables[0].tolist(), "guarded_training_improvements": history[0],
            "evaluation": result,
            "scope": "One additional synthetic team-return fit. The public selector checks legality and "
                     "calibrated receipt rejection across all inventories, then scores eligible schemes "
                     "under the training prior. True held-out inventory priors are evaluation only."}
    if warm:
        report["initialization"] = "Reuse the synthesized both-or-neither policy from the first fit."
    if phase:
        report["fit_method"] = "Exact joint-phase policy improvement on the synthetic guarded reward and training prior."
    return report


if __name__ == "__main__":
    if sys.argv[1:] not in ([], ["--warm"], ["--phase"]):
        raise SystemExit("usage: duplicate_card_guarded_policy.py [--warm | --phase]")
    print(json.dumps(run(warm="--warm" in sys.argv, phase="--phase" in sys.argv), indent=2))
