"""Train a small multi-agent routing repertoire for distinct record rewards."""
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

from duplicate_card_alignment import packets_by_receipt, value_matrix
from duplicate_card_records import FIT
from duplicate_card_routes import MESSAGE_COST, SIGNAL_COST, TRAIN, exact
from duplicate_card_transfer_routes import SKEW
from source_route_search import LEGAL, PRIVATE, PROPOSALS, SEED, UPDATES, play, random_tables

EVIDENCE = FIT.parent
# Values above an empty receipt for [], [first], [second], and [both].
# These are synthetic training rewards, independent of the archived records.
TRAIN_PROFILES = {
    "both_useful": (0, 7, 7, 14),
    "first_only": (0, 7, 0, 7),
    "second_only": (0, 0, 7, 7),
    "both_or_neither": (0, -8, -8, 7),
    "first_unsafe": (0, -8, 7, 7),
    "second_unsafe": (0, 7, -8, 7),
    "first_preferred": (0, 7, 3, 5),
    "second_preferred": (0, 3, 7, 5),
    "withhold": (0, -7, -7, -8),
}
TESTS = {
    "venezuela_raw": ("venezuela_raw", "venezuela_raw"),
    "venezuela_original_release": ("venezuela_original_release", "venezuela_original_release"),
    "venezuela_fields_release": ("venezuela_fields_release", "venezuela_fields_release"),
    "dprk_original_hybrid": ("dprk_original_hybrid", "dprk_original_hybrid"),
    "dprk_reordered_hybrid": ("dprk_reordered_hybrid", "dprk_reordered_hybrid"),
    "dprk_stale_optimistic": ("dprk_reordered_hybrid", "dprk_original_hybrid"),
    "dprk_stale_pessimistic": ("dprk_original_hybrid", "dprk_reordered_hybrid"),
    "venezuela_stale_writer": ("venezuela_original_release", "venezuela_fields_release"),
}
PRIORS = {"uniform": np.ones(16) / 16, "skew": np.outer(*SKEW).flatten()}
# Action 0 is silence and actions 1 and 2 are distinct evidence cards.
RECEIPT = np.bitwise_or.outer([0, 1, 2], [0, 1, 2])
DELIVERY_COST = MESSAGE_COST * np.add.outer([0, 1, 1], [0, 1, 1])


def net_matrix(values):
    return values - DELIVERY_COST


def fit_repertoire(profiles=TRAIN_PROFILES, initial_tables=None):
    rng = np.random.default_rng(SEED)
    matrices = np.stack([net_matrix(np.asarray(scores)[RECEIPT]) for scores in profiles.values()])
    tables = (np.zeros((len(matrices), 2, 4, 5), dtype=np.int8) if initial_tables is None
              else np.array(initial_tables, dtype=np.int8, copy=True))
    assert tables.shape == (len(matrices), 2, 4, 5)
    incumbents = np.array([play(table[None], matrix)[2][0] @ TRAIN
                           for table, matrix in zip(tables, matrices, strict=True)])
    improvements = [[] for _ in matrices]
    for step in range(UPDATES):
        replacements = random_tables(rng)
        slots = rng.random(replacements.shape)
        one_slot = slots.reshape(PROPOSALS, -1).argmin(axis=1)
        mutate = (np.arange(tables[0].size) == one_slot[:, None]).reshape(slots.shape)
        mutate[PROPOSALS // 2:] = slots[PROPOSALS // 2:] < .2
        for i, matrix in enumerate(matrices):
            proposals = np.where(mutate, replacements, tables[i])
            returns = play(proposals, matrix)[2] @ TRAIN
            peak = returns.max()
            if peak >= incumbents[i] - 1e-10:
                tied = np.flatnonzero(np.isclose(returns, peak, rtol=0, atol=1e-10))
                tables[i] = proposals[rng.choice(tied)]
                if peak > incumbents[i] + 1e-10:
                    improvements[i].append({"update": step + 1, "training_return": float(peak)})
                incumbents[i] = max(incumbents[i], peak)
    return tables, improvements


def archived_profiles():
    paths = {name: EVIDENCE / relative for name, relative in {
        "writer": "writer/scores.json", "slots": "slots/scores.json",
        "dprk": "dprk/scores.json", "qualification": "dprk-qualification/scores.json",
    }.items()}
    source = {name: json.loads(path.read_text()) for name, path in paths.items()}
    packets = packets_by_receipt(source["writer"])
    dprk = np.array([r["hybrid_points"] for r in source["dprk"]["four_records"]])
    reordered = np.array([r["authored_plus_reviewed_points"]
                          for r in source["qualification"]["source_order_diagnostic"]["four_records"]])
    assert [r["received"] for r in source["dprk"]["four_records"]] == [[], ["JAPAN"], ["CHINA"], ["JAPAN", "CHINA"]]
    assert [r["received"] for r in source["qualification"]["source_order_diagnostic"]["four_records"]] == [
        r["received"] for r in source["dprk"]["four_records"]
    ]
    matrices = {
        "venezuela_raw": value_matrix(packets, "verified_points"),
        "venezuela_original_release": value_matrix(packets, "release_eligible_points"),
        "venezuela_fields_release": value_matrix(packets_by_receipt(source["slots"]), "release_eligible_points"),
        "dprk_original_hybrid": dprk[RECEIPT],
        "dprk_reordered_hybrid": reordered[RECEIPT],
    }
    return matrices, {str(path.relative_to(EVIDENCE)): sha256(path.read_bytes()).hexdigest()
                      for path in paths.values()}


def rollout(prior, values, signals, actions):
    assert np.all(signals <= ((PRIVATE & 2) != 0)) and np.all(LEGAL[PRIVATE, actions])
    left, right = actions.T
    rewards = values[left, right]
    costs = DELIVERY_COST[left, right] + SIGNAL_COST * signals.sum(axis=1)
    return {
        "net": float(prior @ (rewards - costs)),
        "record_points": float(prior @ rewards),
        "mean_deliveries": float(prior @ (actions != 0).sum(axis=1)),
        "mean_signals": float(prior @ signals.sum(axis=1)),
        "receipt_probabilities": np.bincount(RECEIPT[left, right], weights=prior, minlength=4).tolist(),
        "signals_by_inventory": signals.tolist(), "actions_by_inventory": actions.tolist(),
    }


def test_repertoire(tables, archived_table, matrices):
    result = {}
    for name, (proxy_key, truth_key) in TESTS.items():
        proxy, values = (matrices[key] for key in (proxy_key, truth_key))
        estimate = net_matrix(proxy)
        bits, actions, returns = play(tables, estimate)
        policy_values = returns @ TRAIN
        selected = int(policy_values.argmax())
        silent_cal = exact(TRAIN, estimate, SIGNAL_COST)["silent"][1:]
        archived = [x[0] for x in play(archived_table[None], estimate)[:2]]
        result[name] = {"calibration": proxy_key, "evaluation": truth_key,
                        "template_selected": list(TRAIN_PROFILES)[selected],
                        "calibration_returns": policy_values.tolist(), "priors": {}}
        for prior_name, prior in PRIORS.items():
            exact_controls = exact(prior, net_matrix(values), SIGNAL_COST)
            arms = {f"exact_{key}": rollout(prior, values, signal, delivery)
                    for key, (_, signal, delivery) in exact_controls.items()}
            arms["frozen_proof_router"] = rollout(prior, values, *archived)
            arms["calibrated_silent"] = rollout(prior, values, *silent_cal)
            arms["outcome_repertoire"] = rollout(prior, values, bits[selected], actions[selected])
            assert all(row["net"] <= arms["exact_optional"]["net"] + 1e-9 for row in arms.values())
            result[name]["priors"][prior_name] = arms
    return result


def run():
    tables, history = fit_repertoire()
    matrices, sources = archived_profiles()
    archived_table = np.asarray(json.loads(FIT.read_text())["learned_table"])
    return {
        "scope": "Synthetic team-return policy search, with public protocol selection from archived writer scores. "
                 "Matched calibration uses all four observed receipt scores. Stale calibration deliberately uses a different writer.",
        "training": {"profiles": TRAIN_PROFILES, "prior": TRAIN.tolist(), "seed": SEED,
                     "updates": UPDATES, "proposals": PROPOSALS, "tables": tables.tolist(),
                     "improvements": dict(zip(TRAIN_PROFILES, history, strict=True))},
        "evaluation": test_repertoire(tables, archived_table, matrices),
        "archived_scores": {k: matrix[0, 0].item() for k, matrix in matrices.items()},
        "reward_matrices": {k: matrix.tolist() for k, matrix in matrices.items()},
        "score_artifact_sha256": sources,
        "frozen_proof_policy_sha256": sha256(FIT.read_bytes()).hexdigest(),
        "misspecification_is_a_test": True,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
