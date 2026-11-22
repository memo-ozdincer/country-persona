"""Check reward conditioning on unselected public weight profiles."""
import json
from pathlib import Path

import numpy as np

import estimate_receiver
import reward_receiver as learned
import transfer
import train_calibrator as earlier

HERE = transfer.HERE
SEED = 408117
COUNT = 512


def read(name):
    return json.loads((HERE / name).read_text())


def run():
    calibration = transfer.Calibration()
    fit = read("reward-receiver.json")
    sampled = read("estimated-receiver.json")
    fitted_background = np.asarray(sampled["background"])
    fitted_emission = np.asarray(sampled["emission"])
    decoded = transfer.read("factored-calibration-results.json")["greedy_receiver_table"]
    background = calibration.design_prior.T
    background = background / background.sum(axis=1, keepdims=True)
    _, _, signals = earlier.data(calibration)
    odd = transfer.routing.REQUESTS.sum(axis=1) % 2 == 1
    neutral_signal = signals[odd].mean(axis=0) / (calibration.points[:, 1] - calibration.points[:, 0])
    weights = np.random.default_rng(SEED).integers(0, 36, size=(COUNT, 4))
    if not np.all(weights.any(axis=1)):
        raise ValueError("Public rubric needs at least one positive weight")
    support = np.eye(4)
    aggregated = {}
    methods = ("fixed_gaza", "reward_fit", "both_estimated", "declared_inventory_estimated_channel")
    for name in methods:
        aggregated[name] = {"decision_agreements": 0, "whole_profiles_agree": 0, "regret": []}
    for value in weights:
        oracle = learned.exact(calibration, value)
        reward = neutral_signal * value
        ceiling = float((support[oracle] * reward).sum())
        options = (decoded, learned.decision_table(fit["cover"], fit["likelihood"], value),
                   estimate_receiver.table(fitted_background, fitted_emission, value),
                   estimate_receiver.table(background, fitted_emission, value))
        for label, table in zip(methods, options, strict=True):
            agreed = int((table == oracle).sum())
            achieved = float((support[table] * reward).sum())
            assert achieved <= ceiling + 1e-8
            row = aggregated[label]
            row["decision_agreements"] += agreed
            row["whole_profiles_agree"] += agreed == oracle.size
            row["regret"].append(max(0., ceiling - achieved))
    for row in aggregated.values():
        regret = row.pop("regret")
        row["mean_team_regret"] = float(np.mean(regret))
        row["worst_team_regret"] = max(regret)
    paths = ("reward-receiver.json", "estimated-receiver.json", "probability-audit.json")
    return {"scope": "512 unselected integer weight vectors, each sampled from 0 through 35. "
                     "Degree of agreement is measured for all 192 local decoder states per vector. "
                     "Regret is expected lost team credit on the design prior and held-out odd-parity schedules. "
                     "Both decoder and oracle use the same probe observation and emission uncertainty model except as stated. "
                     "Declared inventory means the existing mean of development priors, never the actual evaluation prior.",
            "code_sha256": transfer.routing.digest(Path(__file__)),
            "source_sha256": {name: transfer.routing.digest(HERE / name) for name in paths},
            "seed": SEED, "weights": weights.tolist(), "profiles": len(weights),
            "decisions_per_profile": oracle.size, "results": aggregated}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
