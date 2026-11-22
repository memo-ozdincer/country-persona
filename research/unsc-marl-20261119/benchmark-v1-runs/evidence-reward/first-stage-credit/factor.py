"""Fit send-or-pass from counterfactual final-record credit with a fixed local sign."""
from pathlib import Path

import learn
import torch

base, E, HERE = learn.base, learn.E, learn.HERE
P = learn.ACTIONS.index("P")


def restrict(logits, allowed):
    return logits.masked_fill(~allowed, float("-inf"))


def fit(x, initial, signed_value, pass_value):
    positives = (signed_value > pass_value).to(x.dtype)
    share = positives.mean()
    assert 0 < float(share) < 1
    weights = .5 * (positives/share + (1-positives)/(1-share))
    head = torch.nn.Parameter(torch.zeros(x.shape[1], dtype=x.dtype))
    optimizer = torch.optim.Adam([head], lr=base.LR)
    trace = []
    for step in range(base.STEPS+1):
        residual = x @ head
        logits = initial + residual
        loss = (weights * torch.nn.functional.binary_cross_entropy_with_logits(
            logits, positives, reduction="none")).mean()
        utility = (logits.sigmoid() * (signed_value - pass_value) + pass_value).mean()
        trace.append({"step": step, "loss": float(loss.detach()), "expected_value": float(utility.detach())})
        if step == base.STEPS:
            break
        optimizer.zero_grad()
        (loss + .002 * residual.square().mean()).backward()
        assert torch.isfinite(head.grad).all()
        optimizer.step()
    return head.detach(), trace


def run():
    torch.set_num_threads(1)
    roster, x, z, _ = base.observations()
    prior = E.read(HERE/"results.json")
    table = E.read(HERE/"reward-table.json")["paths"]
    n = len(roster["train"])
    augmented = [table[split][row["id"]] for split in ("train", "held") for row in roster[split]]
    truth = torch.tensor([learn.ACTIONS.index(row["truthful_action"]) for row in augmented])
    signed_value = torch.tensor([r["reward"][a] for r,a in zip(augmented, truth, strict=True)], dtype=base.DTYPE)
    pass_value = torch.tensor([r["reward"][P] for r in augmented], dtype=base.DTYPE)
    selected = z.gather(1, truth[:, None]).squeeze(1)
    margin = selected - z[:, P]
    w, trace = fit(x[:n], margin[:n], signed_value[:n], pass_value[:n])
    learned = margin + x @ w
    allowed = torch.nn.functional.one_hot(truth, num_classes=3).bool()
    allowed[:, P] = True
    predicted = torch.where(learned > 0, truth, P)
    exact = torch.where(signed_value > pass_value, truth, P)
    decision = z + x @ torch.tensor(prior["weights"]["decision"], dtype=base.DTYPE)
    record = z + x @ torch.tensor(prior["weights"]["record"], dtype=base.DTYPE)
    logits = {"frozen_masked": restrict(z, allowed), "decision_masked": restrict(decision, allowed),
              "record_masked": restrict(record, allowed),
              "learned_send": torch.nn.functional.one_hot(predicted, num_classes=3),
              "exact": torch.nn.functional.one_hot(exact, num_classes=3)}
    outcome = learn.outcomes(roster["held"], {key: val[n:] for key, val in logits.items()}, table["held"])
    assert outcome["summary"]["exact"] == prior["held"]["summary"]["exact"]
    assert all(r["false_sign"] == 0 for r in outcome["summary"].values())
    files = (Path(__file__), HERE/"results.json", HERE/"reward-table.json", HERE/"factor-protocol.md")
    return {"updates": base.STEPS, "qwen_updates": 0, "weights": w.tolist(), "trace": trace,
            "held": outcome, "sha256": {p.name: base.digest(p) for p in files}}


if __name__ == "__main__":
    E.emit(run())
