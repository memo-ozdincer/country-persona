"""Learn a local team-reward receiver, then cross-play on excluded schedules."""
import json
from pathlib import Path
import socket

import numpy as np
import torch

from calibrate_partner import Calibration, HERE, read
import routing

SEED = 20231121
STEPS = 96
HORIZON = 8
DT = torch.float64


def data(calibration):
    probes = routing.REQUESTS
    pair_mask = routing.OPTIONS.astype(float)
    design = calibration.design_prior
    # One public probe per focus. Reward is the actual soft expected team return
    # from choosing each legal annex. No exact-calibrator labels enter the fit.
    features = []
    for reply in probes:
        for mask in pair_mask:
            for observed in range(2):
                features.append([*reply, *mask, observed])
    branch_probability = []
    team_signal = []
    for sender in probes:
        chance_of_request = sender * (1 - calibration.question_loss)
        outcome = np.prod(np.where(probes, chance_of_request, 1 - chance_of_request), axis=1)
        arrived = np.stack([1 - chance_of_request, chance_of_request])
        value = ((1 - calibration.reply_loss) * design.T[:, None, :] * arrived[None, :, :]
                 * (calibration.points[:, 1] - calibration.points[:, 0]))
        branch_probability.append(outcome)
        team_signal.append(outcome[:, None, None, None] * value)
    return np.asarray(features), np.asarray(branch_probability), np.asarray(team_signal)


def train(features, rewards):
    torch.set_num_threads(1)
    torch.manual_seed(SEED)
    network = torch.nn.Sequential(torch.nn.Linear(9, 24, dtype=DT), torch.nn.Tanh(),
                                  torch.nn.Linear(24, 4, dtype=DT))
    optimizer = torch.optim.Adam(network.parameters(), lr=.035)
    batch = torch.as_tensor(features, dtype=DT)
    allowed = torch.as_tensor(routing.OPTIONS[None, :, None, :])
    target = torch.as_tensor(rewards, dtype=DT)
    trajectory = []
    table = None
    for step in range(STEPS + 1):
        output = network(batch).reshape(16, 6, 2, 4).masked_fill(~allowed, -torch.inf)
        policy = output.softmax(dim=-1)
        expected = (policy * target).sum()
        trajectory.append(float(expected.detach()))
        if step == 0:
            initial = output.argmax(dim=-1).detach().numpy()
        if step == STEPS:
            table = output.argmax(dim=-1).detach().numpy()
            break
        optimizer.zero_grad()
        (-expected).backward()
        assert all(torch.isfinite(parameter.grad).all() for parameter in network.parameters())
        optimizer.step()
    return initial, table, trajectory


def evaluate(table, calibration, branch_probability):
    report = {}
    for i, sender in enumerate(routing.REQUESTS):
        probability = branch_probability[i]
        assert np.isclose(probability.sum(), 1.)
        fee = .2 + calibration.question_fee * sender.sum()
        name = "".join(map(str, sender))
        report[name] = {prior: float(sum(mass * calibration.utility(sender, receiver, distribution)
                                         for mass, receiver in zip(probability, table, strict=True) if mass > 0)
                                      - fee / HORIZON)
                        for prior, distribution in calibration.priors.items()}
    return report


def run():
    calibration = Calibration()
    features, branches, labels = data(calibration)
    training = routing.REQUESTS.sum(axis=1) % 2 == 0
    initial, greedy, history = train(features, labels[training].mean(axis=0))
    initial_eval = evaluate(initial, calibration, branches)
    observed = evaluate(greedy, calibration, branches)
    info = read("calibration-results.json")["results"][str(HORIZON)]["by_sender"]
    assert info.keys() == observed.keys()
    result = {}
    measures = {}
    primary = "correlated_development"
    for name, evaluation in observed.items():
        result[name] = {"split": "train" if name.count("1") % 2 == 0 else "excluded",
                        "initial": initial_eval[name], "learned": evaluation,
                        "same_probe_exact_decoding": info[name]["one_each"]["net_scores"],
                        "known_sender_bound": info[name]["known_sender_informed"]["net_scores"]}
    for split in ("train", "excluded"):
        subset = [row for row in result.values() if row["split"] == split]
        measures[split] = {method: float(np.mean([row[method][primary] for row in subset]))
                           for method in ("initial", "learned", "same_probe_exact_decoding", "known_sender_bound")}
    assert all(row["learned"][p] <= row["known_sender_bound"][p] + 1e-8
               for row in result.values() for p in calibration.priors)
    return {"scope": "One fixed four-probe deck, with original request erasure and fees. "
                     "Train via expected shared reward on eight even-parity requester schedules. "
                     "All eight odd-parity schedules are excluded, including both archived cross-play senders. "
                     "The script comparison conditions on the same delivered observations and fees.",
            "host": socket.gethostname(), "device": "CPU", "seed": SEED, "optimizer_steps": STEPS,
            "code_sha256": routing.digest(Path(__file__)), "calibration_sha256": routing.digest(HERE / "calibration-results.json"),
            "training_bonus_by_step": history, "greedy_receiver_table": greedy.tolist(),
            "means_on_development_prior": measures, "evaluations": result}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
