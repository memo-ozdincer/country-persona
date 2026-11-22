"""Fit a calibrated receiver that sees the announced value of each source."""
from itertools import permutations
import json
from pathlib import Path

import numpy as np
import torch

import transfer
import train_calibrator as earlier

HERE = transfer.HERE
DT = torch.float64
SEED = earlier.SEED
UPDATES = 96
TRAIN = np.asarray(sorted(set(permutations((7, 14, 21, 28)))), dtype=float)
TEST = {
    "gaza": [28, 28, 21, 28],
    "jerusalem": [28, 28, 28, 28],
    "sparse": [28, 0, 14, 21],
    "unequal": [5, 11, 19, 29],
    "favor_fourth": [7, 7, 7, 28],
    "favor_second": [14, 28, 14, 14],
}


def logits(cover, likelihood):
    probes = torch.as_tensor(transfer.routing.REQUESTS, dtype=torch.long)
    query = torch.arange(2)[None, None, :, None]
    return cover[None, :, None, :] + likelihood[probes[:, None, None, :], query]


def train(calibration):
    torch.set_num_threads(1)
    torch.manual_seed(SEED)
    cover = torch.nn.Parameter(.02 * torch.randn(6, 4, dtype=DT))
    likelihood = torch.nn.Parameter(.02 * torch.randn(2, 2, dtype=DT))
    allow = torch.as_tensor(transfer.routing.OPTIONS[None, :, None, :])
    optimizer = torch.optim.Adam([cover, likelihood], lr=.035)
    _, _, old_signals = earlier.data(calibration)
    schedule_split = transfer.routing.REQUESTS.sum(axis=1) % 2 == 0
    signal = old_signals[schedule_split].mean(axis=0) / (calibration.points[:, 1] - calibration.points[:, 0])
    values = torch.as_tensor(TRAIN[:, None, None, None, :], dtype=DT)
    expected_credit = torch.as_tensor(signal[None], dtype=DT) * values
    history = []
    for step in range(UPDATES + 1):
        score = (logits(cover, likelihood)[None] + values.log()).masked_fill(~allow, -torch.inf)
        credit = (score.softmax(dim=-1) * expected_credit).sum() / len(TRAIN)
        history.append(float(credit.detach()))
        if step == UPDATES:
            break
        optimizer.zero_grad()
        (-credit).backward()
        assert torch.isfinite(cover.grad).all() and torch.isfinite(likelihood.grad).all()
        optimizer.step()
    return cover.detach().numpy(), likelihood.detach().numpy(), history


def decision_table(cover, likelihood, marginal):
    assert np.all(np.isfinite(marginal)) and np.all(np.asarray(marginal) >= 0)
    background = logits(torch.as_tensor(cover), torch.as_tensor(likelihood)).numpy()
    reward = np.log(np.maximum(marginal, np.finfo(float).tiny))
    return np.where(transfer.routing.OPTIONS[None, :, None, :], background + reward, -np.inf).argmax(axis=-1)


def exact(calibration, marginal):
    calibration.points[:, 1] = 42 + np.asarray(marginal)
    tables = []
    for row in transfer.routing.REQUESTS:
        state = tuple(-1 if observed else 1 for observed in row)
        tables.append(calibration.receiver(calibration.probabilities(state), calibration.design_prior))
    return np.asarray(tables)


def run():
    calibration = transfer.Calibration()
    cover, likelihood, rewards = train(calibration)
    _, branches, _ = earlier.data(calibration)
    frozen = np.asarray(transfer.read("factored-calibration-results.json")["greedy_receiver_table"])
    tests = {}
    for name, marginal in TEST.items():
        assert not np.any(np.all(TRAIN == marginal, axis=1))
        learned = decision_table(cover, likelihood, marginal)
        reference = exact(calibration, marginal)
        case = {key: earlier.evaluate(table, calibration, branches) for key, table in
                (("learned", learned), ("exact", reference), ("fixed_gaza", frozen))}
        heldout = [key for key in case["learned"] if key.count("1") % 2]
        comparisons = {prior: [case["learned"][key][prior] - case["exact"][key][prior] for key in heldout]
                       for prior in calibration.priors}
        tests[name] = {"same_actions": int((learned == reference).sum()), "total_actions": reference.size,
                       "old_actions_equal": int((frozen == reference).sum()),
                       "heldout_net_difference_range": [min(map(min, comparisons.values())),
                                                        max(map(max, comparisons.values()))],
                       "metrics": case}
    return {"scope": "One CPU fit using simulated Gaza priors, even-parity partners and all 24 permutations of "
                     "four synthetic reward weights. The test vectors and odd-parity partners are excluded. "
                     "Predictions use disclosed reward magnitudes. No writer judgments or decoder labels enter training.",
            "seed": SEED, "steps": UPDATES, "code_sha256": transfer.routing.digest(Path(__file__)),
            "prior_decoder_sha256": transfer.routing.digest(transfer.GAZA / "factored-calibration-results.json"),
            "train_weights": TRAIN.tolist(), "reward_history": rewards, "cover": cover.tolist(),
            "likelihood": likelihood.tolist(), "tests": tests}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
