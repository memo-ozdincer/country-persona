"""Learn a local policy from fresh receipt-conditioned record scores."""
import argparse
import json
from pathlib import Path

import numpy as np

from duplicate_card_outcome_policy import SEED, UPDATES, PROPOSALS, TRAIN, fit_repertoire
from duplicate_card_routes import exact
from duplicate_card_semantic_review import EVIDENCE, SIGNAL_COST, digest
from minurso_receipt_scores import PRIVATE, matrix_by_loss, play


def report(score_path):
    receipt_scores = json.loads(score_path.read_text())
    by_receipt = tuple(item["eligible_points"] for item in receipt_scores["receipts"])
    assert len(set(by_receipt)) > 1, "The measured endpoint has no receipt-dependent reward."
    prior_path = EVIDENCE / "dprk-routes.json"
    priors = {name: np.array([r["probability"] for r in value["silent"]["worlds"]])
              for name, value in json.loads(prior_path.read_text())["arms"].items()}
    tables, traces = fit_repertoire({"minurso": by_receipt})
    fit = tables[0]
    train = play(fit, TRAIN, by_receipt, 0.)
    train_bounds = exact(TRAIN, matrix_by_loss(by_receipt, 0.), SIGNAL_COST)
    assert train["net"] <= train_bounds["optional"][0] + 1e-9
    transferred_path = EVIDENCE / "buffered-fit.json"
    transferred = np.asarray(json.loads(transferred_path.read_text())["trained_tables"]["matched"])
    world_differences = []
    for j, pair in enumerate(PRIVATE):
        point_mass = np.eye(len(PRIVATE))[j]
        fitted_return = play(fit, point_mass, by_receipt, 0.)
        transferred_return = play(transferred, point_mass, by_receipt, 0.)
        difference = fitted_return["net"] - transferred_return["net"]
        if not np.isclose(difference, 0.):
            world_differences.append({"inventories": pair.tolist(), "net_difference": difference})
    comparisons = []
    for item in receipt_scores["rollout"]:
        if item["reward"] != "guarded_actual":
            continue
        observed = play(fit, priors[item["prior"]], by_receipt, item["loss"])
        arms = item["arms"]
        assert observed["net"] <= arms["optional_ceiling"]["net"] + 1e-9
        comparisons.append({"prior": item["prior"], "loss": item["loss"], "learned": observed,
                            "same_writer_silence": arms["optimal_silence"],
                            "same_writer_optional_ceiling": arms["optional_ceiling"],
                            "frozen_buffer": arms["frozen_buffer"],
                            "frozen_additive": arms["frozen_additive"],
                            "gain": observed["net"] - arms["optimal_silence"]["net"]})
    return {
        "scope": "Team-reward table search with fresh generated and manually assessed final records as a fixed payoff. "
                 "The writers are frozen. Fit is lossless on a third inventory prior. Evaluations vary the inventory prior "
                 "and independent link losses on the same case. The desks observe typed evidence availability.",
        "scores_sha256": digest(score_path), "prior_sha256": digest(prior_path),
        "transferred_policy_sha256": digest(transferred_path), "payoffs": by_receipt,
        "search": {"seed": SEED, "updates": UPDATES, "proposals": PROPOSALS,
                   "training_prior": TRAIN.tolist(), "loss": 0., "improvements": traces[0]},
        "table": fit.tolist(), "training_result": train,
        "training_ceiling": train_bounds["optional"][0],
        "training_silent": train_bounds["silent"][0], "comparisons": comparisons,
        "world_differences_from_transfer_at_zero_loss": world_differences,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("score", type=Path)
    print(json.dumps(report(p.parse_args().score), indent=2))
