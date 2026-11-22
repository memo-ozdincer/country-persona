"""Fit two decentralized policies for the corroborating verified-record reward."""
from hashlib import sha256
import json
from pathlib import Path
import socket

import numpy as np
import torch

import corroboration_receiver as receiver

HERE = receiver.HERE
UPDATES = 96
SEED = 20231120
DT = torch.float64


def train(calibration, gain, bare):
    torch.set_num_threads(1)
    rng = torch.Generator().manual_seed(SEED)
    sender = torch.nn.Parameter(.02 * torch.randn(4, 2, dtype=DT, generator=rng))
    reply = torch.nn.Parameter(.02 * torch.randn(6, 2, 2, dtype=DT, generator=rng))
    optim = torch.optim.Adam([sender, reply], lr=.12)
    prior = torch.as_tensor(calibration.design_prior, dtype=DT)
    payload = torch.as_tensor(gain[:, receiver.transfer.routing.PAIR], dtype=DT)
    protected = torch.as_tensor(bare, dtype=DT)
    history = []
    for step in range(UPDATES + 1):
        sending = sender.softmax(dim=-1)
        delivered = (1 - calibration.question_loss) * sending + calibration.question_loss * torch.tensor([1., 0.], dtype=DT)
        selected = reply.softmax(dim=-1)
        reward = (protected - calibration.question_fee * sending[:, 1]) @ prior.sum(dim=1)
        reward += (1 - calibration.reply_loss) * torch.einsum("fr,fq,rqa,fra->", prior, delivered, selected, payload)
        reward -= calibration.reply_fee
        history.append(float(reward.detach()))
        if step == 0:
            initial = extract(sender, reply)
        if step == UPDATES:
            break
        optim.zero_grad()
        (-reward).backward()
        assert torch.isfinite(sender.grad).all() and torch.isfinite(reply.grad).all()
        optim.step()
    return initial, extract(sender, reply), history


def extract(sender, reply):
    choices = reply.detach().argmax(dim=-1).numpy()
    return sender.detach().argmax(dim=-1).numpy(), receiver.transfer.routing.PAIR[np.arange(6)[:, None], choices]


def blueprint(calibration, gain, bare):
    design = calibration.design_prior
    scripts = {}
    for kind, sender in (("blind_silent", np.zeros(4, dtype=int)),
                         *((name, np.asarray(desk["mission"])) for name, desk in receiver.DIRECT.items())):
        replies = receiver.policy(receiver.known_probability(sender, calibration.question_loss), design, gain)
        scripts[kind] = (sender, replies)
    candidates = [(sender, receiver.policy(receiver.known_probability(sender, calibration.question_loss), design, gain))
                  for sender in receiver.transfer.routing.REQUESTS]
    scripts["development_exact"] = max(candidates, key=lambda table: receiver.utility(*table, design, gain, bare, calibration))
    return scripts


def run():
    source = HERE / "corroboration-records.json"
    records = receiver.case.read(source)
    assert json.loads(json.dumps(receiver.case.bank())) == records
    bare = np.asarray(records["bare_scores"])
    scores = np.asarray(records["joint_scores"])
    gain = scores - bare[:, None]
    calibration = receiver.transfer.Calibration()
    start, fitted, trace = train(calibration, gain, bare)
    controls = blueprint(calibration, gain, bare)
    policies = {"initial": start, "learned": fitted, **controls}
    outcomes = {}
    priors = {"design_mixture": calibration.design_prior, **calibration.priors}
    for name, prior in priors.items():
        out = {method: receiver.utility(*table, prior, gain, bare, calibration) for method, table in policies.items()}
        out["learned_mission_erased"] = receiver.utility(*fitted, prior, gain, bare, calibration, loss=1.)
        out.update(receiver.bound(prior, gain, bare, calibration))
        best_received = gain[:, receiver.transfer.routing.PAIR].max(axis=-1)
        out["full_local_inventories"] = float((prior * (bare[:, None] + (1 - calibration.reply_loss)
                                                       * best_received)).sum() - calibration.reply_fee)
        assert all(score <= out["full_local_inventories"] + 1e-9 for score in out.values())
        assert max(value for key, value in out.items() if key != "full_local_inventories") <= out["prior_informed_interactive"] + 1e-9
        outcomes[name] = out
    assert np.isclose(outcomes["design_mixture"]["development_exact"],
                      outcomes["design_mixture"]["prior_informed_interactive"])
    return {"scope": "One shared-reward fit. The requester reads its authenticated focal card identity, "
                     "and the responder reads its local inventory and any delivered request bit. Both policies "
                     "train on the declared mean of archived development priors. The strong exact scripts optimize "
                     "under the same development prior. The separate informed upper bounds know each evaluation prior.",
            "code_sha256": sha256(Path(__file__).read_bytes()).hexdigest(), "registry_sha256": sha256(source.read_bytes()).hexdigest(),
            "host": socket.gethostname(), "torch": torch.__version__, "device": "CPU", "seed": SEED, "updates": UPDATES,
            "expected_reward_trajectory": trace,
            "policies": {name: [value.tolist() for value in policy] for name, policy in policies.items()},
            "outcomes": outcomes}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
