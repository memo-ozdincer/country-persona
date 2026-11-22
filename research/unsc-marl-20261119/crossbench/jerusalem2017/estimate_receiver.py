"""Estimate a calibrated observation model from sampled team rollouts."""
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

import reward_receiver as reward
import transfer
import train_calibrator as earlier

ROLLOUTS = 4096
SEED = 20231122


def sample(calibration):
    rng = np.random.default_rng(SEED)
    schedules = transfer.routing.REQUESTS
    train = schedules[schedules.sum(axis=1) % 2 == 0]
    sender = train[rng.integers(len(train), size=ROLLOUTS)]
    world = rng.choice(24, size=ROLLOUTS, p=calibration.design_prior.ravel())
    focus, pair = np.unravel_index(world, (4, 6))
    probes = sender * (rng.random((ROLLOUTS, 4)) >= calibration.question_loss)
    mission = sender[np.arange(ROLLOUTS), focus] * (rng.random(ROLLOUTS) >= calibration.question_loss)
    observed_focal_probe = probes[np.arange(ROLLOUTS), focus]
    return np.c_[focus, pair, probes, mission].astype(np.uint8), observed_focal_probe


def fit(rollouts, focal_probe):
    focus, pair, mission = rollouts[:, 0], rollouts[:, 1], rollouts[:, -1]
    background = np.zeros((6, 4), dtype=int)
    emitted = np.zeros((2, 2), dtype=int)
    np.add.at(background, (pair, focus), 1)
    np.add.at(emitted, (focal_probe, mission), 1)
    assert background.sum() == emitted.sum() == ROLLOUTS
    # Smooth counts without revealing the simulator's true prior or sender.
    background_p = (background + .5) / (background.sum(axis=1, keepdims=True) + 2)
    emission_p = (emitted + .5) / (emitted.sum(axis=1, keepdims=True) + 1)
    return background, emitted, background_p, emission_p


def table(background, emission, marginal):
    probe = transfer.routing.REQUESTS
    likelihood = np.stack((emission[probe, 0], emission[probe, 1]), axis=1)
    local = background[None, :, None, :] * likelihood[:, None, :, :] * np.asarray(marginal)
    return np.where(transfer.routing.OPTIONS[None, :, None, :], local, -1).argmax(axis=-1)


def run():
    calibration = transfer.Calibration()
    rows, observed = sample(calibration)
    counts, emitted, background, emission = fit(rows, observed)
    _, branches, _ = earlier.data(calibration)
    objective = json.loads((transfer.HERE / "reward-receiver.json").read_text())
    tests = {}
    for name, marginal in reward.TEST.items():
        inferred = table(background, emission, marginal)
        truth = reward.exact(calibration, marginal)
        out = earlier.evaluate(inferred, calibration, branches)
        known = objective["tests"][name]["metrics"]["exact"]
        assert all(np.isclose(known[desk][prior], out_score) for desk, row in
                   earlier.evaluate(truth, calibration, branches).items() for prior, out_score in row.items())
        heldout = [key for key in out if key.count("1") % 2]
        gap = [out[desk][prior] - known[desk][prior] for desk in heldout for prior in calibration.priors]
        tests[name] = {"same_actions": int((inferred == truth).sum()), "total_actions": truth.size,
                       "heldout_net_difference_range": [min(gap), max(gap)], "scores": out}
    return {"scope": "A model-based comparator, not an additional team-reward fit. Learn an inventory-conditioned "
                     "focus distribution and a shared probe/request likelihood from centralized sampled traces. "
                     "Execution sees local inventory, probe outcomes, the delivered request and public weights. "
                     "Even-parity senders only enter estimation. No evaluation labels or writer scores enter it.",
            "code_sha256": transfer.routing.digest(Path(__file__)),
            "team_reward_fit_sha256": transfer.routing.digest(transfer.HERE / "reward-receiver.json"),
            "seed": SEED, "sampled_rollouts": ROLLOUTS, "sample_sha256": sha256(rows.tobytes()).hexdigest(),
            "counts": counts.tolist(), "emission_counts": emitted.tolist(), "background": background.tolist(),
            "emission": emission.tolist(), "tests": tests}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
