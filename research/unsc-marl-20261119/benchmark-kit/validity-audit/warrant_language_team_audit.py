"""Check normalization, omission handling and frozen-receiver parity."""
import json

import numpy as np

import warrant_language_team_score as score

study, world = score.study, score.world


def run():
    cards = next(study.domains())
    task = world.Workshop(cards)
    styles = study.fitted(task)
    assignment = styles["mixed"]
    p = world.prior(False)
    draws = np.random.default_rng(score.adapt.SEED).random((score.adapt.REPLICAS, score.adapt.STEPS[-1]))
    u, mass = score.actual_values(task, p, assignment)
    reference = score.receiver.measurement(task, p,
        np.asarray(json.loads(study.design.PREVIOUS.read_text())["fitted_weights"]), styles["fitted"], draws)
    result = score.predict(task, p, styles, u, mass, draws)
    assert abs(result["blend/16"]["mean_net"] - reference["mixed"]["mean_net"]) < 1e-12
    suppressed = assignment.copy()
    suppressed[0, 0] = -1
    evidence, probability = score.actual_values(task, p, suppressed)
    assert np.isclose(probability.sum(), 1.)
    assert evidence[:, 0].sum() <= u[:, 0].sum() + 1e-12
    synthetic = {}
    for role, card in np.ndindex(3, 4):
        slot = assignment[role, card]
        text = study.phrases.wire(role, slot, cards[role, card, slot])
        synthetic[f"d0/D{role+1}/card{card}"] = {"ended": True, "output": text, "input_ids": [], "output_ids": []}
    altered = synthetic["d0/D1/card0"]
    altered["output"] = altered["output"].replace("D1", "D2", 1)
    observed, _ = score.reports(synthetic, 0, cards, assignment)
    assert np.array_equal(observed, suppressed)
    return {"software_check_only": True, "parity_with_frozen_mixed_receiver": True,
            "wrong_speaker_rejected": True, "loss_distribution_normalized_after_rejection": True}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
