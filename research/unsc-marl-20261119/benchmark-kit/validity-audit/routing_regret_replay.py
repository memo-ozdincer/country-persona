"""Replay the paired group fit and diagnose fixed-policy losses."""
import argparse
import json
from pathlib import Path

import numpy as np
import torch

import routing_regret_training as training

base, route, digest = training.base, training.route, training.digest


def verify(directory):
    report = json.loads((directory / "report.json").read_text())
    launch = json.loads((directory / "launch.json").read_text())
    paths = (Path(training.__file__), Path(training.sampled.__file__), Path(route.__file__),
             Path(training.paired.__file__), Path(base.__file__), training.PRIORS,
             training.PREVIOUS / "report.json")
    assert launch["locks"] == {path.name: digest(path) for path in paths}
    profiles = training.paired.curriculum()
    priors = training.training_priors()
    np.testing.assert_array_equal(profiles, report["training_profiles"])
    np.testing.assert_array_equal(priors, report["train_priors"])
    refit, curve = training.fit(profiles, priors)
    assert curve == report["training_checkpoints"]
    frozen = {}
    for arm, sha in report["weight_sha256"].items():
        path = directory / f"{arm}.pt"
        assert digest(path) == sha
        model = training.paired.contrasts.load(path)
        assert all(torch.equal(param, refit[arm].state_dict()[key]) for key, param in model.state_dict().items())
        frozen[arm] = model
    archive = json.loads(training.PRIORS.read_text())
    earlier = json.loads((training.PREVIOUS / "report.json").read_text())
    restored = training.evaluate(frozen, archive, earlier)
    assert restored == report["historical_replay"]

    bank = {name: np.asarray(p) for group in ("prior_anchors", "prior_stress") for name, p in archive[group].items()}
    diagnosis = {}
    for case, sha, _, actual in base.held_out():
        assert restored[case]["source_sha256"] == sha
        file = restored[case]
        old_policy = base.space.as_policy(file["policies"]["uniform_training"])
        diagnosis[case] = {}
        for name, prior in bank.items():
            old = file["priors"][name]["arms"]["uniform_training"]
            shuffled = route.evaluate(old_policy, (prior + prior.T) / 2, actual, route.TRAIN_LOSS)
            diagnosis[case][name] = {
                "uniform_training_minus_informed_independence": old["new_value_vs_independence"],
                "uniform_training_request_erasure_drop": old["request_value_vs_erasure"],
                "uniform_training_fair_requester_minus_informed_independence": (
                    shuffled["net"] - file["priors"][name]["optimized_independence"]
                ),
            }
    cells = [row for priors in diagnosis.values() for row in priors.values()]
    losses = [row for row in cells if row["uniform_training_minus_informed_independence"] < -1e-9]
    return {
        "report_sha256": digest(directory / "report.json"), "refit_tensor_equality": True,
        "all_historical_scores_equal": True, "uniform_training_losses": len(losses),
        "uniform_training_losses_with_positive_request_value": sum(
            row["uniform_training_request_erasure_drop"] > 1e-9 for row in losses),
        "diagnosis": diagnosis,
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    print(json.dumps(verify(cli.parse_args().directory), indent=2))
