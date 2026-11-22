"""Fit local action-logit residuals against a shared buffered-record reward."""
from hashlib import sha256
import json

import numpy as np
import torch

from duplicate_card_buffered_fit import PAIR_REWARD, TRAIN_FAILURE, action_matrix
from duplicate_card_language import CASES, POLICY, inputs, scorer
from duplicate_card_outcome_policy import EVIDENCE, PRIORS, PRIVATE, TRAIN, archived_profiles
from duplicate_card_transport import FAULTS, MASKS, mask_weight, simulate
from source_route_search import LEGAL, SIGNAL_COST

ACTIONS = EVIDENCE / "language"
STEPS = 240
LR = .075
SEAT_INDEX = torch.arange(2)
INVENTORY = torch.from_numpy(PRIVATE)
SIGNAL_LEGAL = torch.tensor([[True, bool(x & 2)] for x in range(4)])
DELIVERY_LEGAL = torch.from_numpy(LEGAL[:, None, None, :])
DTYPE = torch.float64


def read_base():
    with inputs():
        rows = scorer.read(ACTIONS)
    base = {}
    for case in CASES:
        signal = torch.zeros((2, 4, 2), dtype=DTYPE)
        delivery = torch.zeros((2, 4, 2, 2, 3), dtype=DTYPE)
        for (name, phase, seat, inventory, own, peer), row in rows.items():
            if name != case:
                continue
            scores = torch.as_tensor(row["scores"], dtype=DTYPE)
            if phase == "signal":
                signal[seat, inventory] = scores - scores.mean()
            else:
                delivery[seat, inventory, own, peer] = scores - scores.mean()
        base[case] = (signal, delivery)
    return base


def probabilities(base, correction, silent=False):
    sig, delivery = (x + y for x, y in zip(base, correction, strict=True))
    legal = SIGNAL_LEGAL if not silent else torch.tensor([[True, False]] * 4)
    return sig.masked_fill(~legal, -torch.inf).softmax(-1), delivery.masked_fill(~DELIVERY_LEGAL, -torch.inf).softmax(-1)


def return_by_world(signal, delivery, rates, pair_reward):
    signal_fail, delivery_fail = rates
    local_signal = signal[SEAT_INDEX, INVENTORY]
    matrix = torch.as_tensor(action_matrix(pair_reward, delivery_fail), dtype=DTYPE)
    reward = torch.zeros(len(INVENTORY), dtype=DTYPE)
    for left, right in MASKS:
        choice = local_signal[:, 0, left] * local_signal[:, 1, right]
        payoff = torch.zeros_like(reward)
        for seen in MASKS:
            q = delivery[0, INVENTORY[:, 0], left, right * seen[0]]
            r = delivery[1, INVENTORY[:, 1], right, left * seen[1]]
            payoff += mask_weight(seen, signal_fail) * torch.einsum("ni,ij,nj->n", q, matrix, r)
        reward += choice * (payoff - SIGNAL_COST * (left + right))
    return reward


def expected(base, correction, prior, rates, pair_reward, silent=False):
    strategy = probabilities(base, correction, silent)
    return torch.as_tensor(prior, dtype=DTYPE) @ return_by_world(*strategy, rates, pair_reward)


def fit(base, silent=False, shared_by_peer=False):
    if shared_by_peer:
        initial = (base[0][:, :1], base[1][:, :1, :1])
        check = (0, 0, 0, 0, 1)
    else:
        initial = base
        check = (0, 3, 0, 0, 1)
    correction = tuple(torch.nn.Parameter(torch.zeros_like(t)) for t in initial)
    optim = torch.optim.Adam(correction, lr=LR)

    def train():
        return expected(base, correction, TRAIN, TRAIN_FAILURE, PAIR_REWARD, silent)

    first = float(train().detach())
    derivative = float(torch.autograd.grad(train(), correction[1])[0][check])
    with torch.no_grad():
        correction[1][check] = 1e-5
        positive = float(train())
        correction[1][check] = -1e-5
        negative = float(train())
        correction[1][check] = 0
    finite_difference = (positive - negative) / 2e-5
    assert abs(derivative - finite_difference) < 1e-8
    history = []
    for step in range(1, STEPS + 1):
        utility = train()
        optim.zero_grad()
        (-utility).backward()
        assert all(t.grad is not None and torch.isfinite(t.grad).all() for t in correction)
        gradient = float(sum(t.grad.square().sum() for t in correction).sqrt())
        optim.step()
        if step in (1, 10, 40, 80, 120, STEPS):
            history.append({"step": step, "training_return_before_update": float(utility.detach()),
                            "gradient_norm": gradient})
    return tuple(t.detach() for t in correction), {
        "initial_expected_return": first, "final_expected_return": float(train().detach()),
        "gradient_check": {"automatic": derivative, "finite_difference": finite_difference},
        "trace": history,
    }


def decision_table(probs):
    signal, delivery = (x.detach().argmax(-1).cpu().numpy() for x in probs)
    return np.concatenate([signal[..., None], delivery.reshape(2, 4, 4)], axis=-1)


def run():
    torch.set_num_threads(1)
    base = read_base()
    train_case = base["venezuela"]
    zeros = tuple(torch.zeros_like(t) for t in train_case)
    models = {}
    for name, init, silent in (
        ("qwen_residual", train_case, False),
        ("tabular_from_zero", zeros, False),
        ("qwen_residual_silent", train_case, True),
    ):
        models[name] = (*fit(init, silent), silent)
    old_fit = json.loads(POLICY.read_text())
    typed = np.asarray(old_fit["trained_tables"]["matched"])
    values, score_hashes = archived_profiles()
    archived = {"venezuela": values["venezuela_original_release"], "dprk": values["dprk_reordered_hybrid"]}
    output = {}
    for case, observed in base.items():
        strategies = {"frozen_qwen": probabilities(observed, zeros)}
        for mode, (correction, _, silent) in models.items():
            start = zeros if mode == "tabular_from_zero" else observed
            strategies[mode] = probabilities(start, correction, silent)
        strategies["isolated_residual"] = probabilities(zeros, models["qwen_residual"][0])
        tables = {k: decision_table(p) for k, p in strategies.items()}
        evaluation = {}
        for prior, distribution in PRIORS.items():
            evaluation[prior] = {}
            for condition in ("none", "both_10", "both_25"):
                rates = FAULTS[condition]
                matrix = archived[case]
                baseline_offset = matrix[0, 0]
                pair_gain = matrix[1, 2] - baseline_offset
                best_silent = old_fit["priors"][prior][condition]["exact_buffered_silent"]["net"]
                assert pair_gain == 14 and baseline_offset >= 35
                stats = {"typed": simulate(typed, distribution, matrix, *rates)["writer"]["buffered"]["net"],
                         "exact_silent": best_silent + baseline_offset - 35}
                for name, probs in strategies.items():
                    stochastic = torch.as_tensor(distribution) @ return_by_world(*probs, rates, pair_gain)
                    greedy = simulate(tables[name], distribution, matrix, *rates)["writer"]["buffered"]
                    stats[name] = {"greedy_net": greedy["net"], "stochastic_net": float(stochastic) + baseline_offset,
                                   "both_cards_probability": greedy["writer_receipts"][3]}
                decision = tables["qwen_residual"]
                stats["residual_with_typed_partner"] = [
                    simulate(pair, distribution, matrix, *rates)["writer"]["buffered"]["net"]
                    for pair in (np.stack((decision[0], typed[1])), np.stack((typed[0], decision[1])))
                ]
                evaluation[prior][condition] = stats
        output[case] = {"role": "fit" if case == "venezuela" else "held_out_from_fit",
                        "greedy_tables": {k: t.tolist() for k, t in tables.items()}, "evaluation": evaluation}
    return {"scope": "Exact team-reward optimization with decentralized local action-logit corrections. "
                     "The Qwen backbone and cached logits are frozen. DPRK action scores are held out from fitting.",
            "steps": STEPS, "learning_rate": LR, "training_faults": TRAIN_FAILURE, "pair_reward": PAIR_REWARD,
            "training_prior": TRAIN.tolist(), "training": {
                name: {**r, "corrections": [t.tolist() for t in correction]}
                for name, (correction, r, _) in models.items()},
            "archived_actions_sha256": sha256((ACTIONS / "actions.jsonl").read_bytes()).hexdigest(),
            "typed_policy_sha256": sha256(POLICY.read_bytes()).hexdigest(),
            "score_hashes": score_hashes, "cases": output}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
