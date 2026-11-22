"""Calibrate the existing responder logits from signed counterfactual value."""
from pathlib import Path

import torch

import reply_coverage
import study

HERE = study.HERE
E = study.benchmark


def solve(roles):
    _, features, reachable, delta, _ = study.tensors(roles)
    idx = reachable > 0
    features = features[idx]
    good = (delta[idx] > 0).to(features.dtype)
    assert 0 < float(good.sum()) < len(good)
    prevalence = good.mean()
    balance = .5 * (good / prevalence + (1-good) / (1-prevalence))
    model = torch.nn.Parameter(torch.zeros(features.shape[1], dtype=study.DTYPE))
    opt = torch.optim.Adam([model], lr=.12)
    trace = []
    for step in range(study.UPDATES + 1):
        logit = features @ model
        losses = torch.nn.functional.binary_cross_entropy_with_logits(logit, good, reduction="none")
        loss = (balance * losses).mean()
        trace.append({"step": step, "loss": float(loss.detach()),
                      "training_errors": int(((logit > 0) != good.bool()).sum())})
        if step == study.UPDATES:
            break
        opt.zero_grad()
        (loss + .001 * model.square().mean()).backward()
        assert torch.isfinite(model.grad).all()
        opt.step()
    return model.detach(), trace


def run():
    torch.set_num_threads(1)
    train, test = study.roster()
    file = HERE / "results.json"
    earlier = E.read(file)
    chair = torch.tensor(earlier["weights"][0], dtype=study.DTYPE)
    calibrated, trace = solve(train)
    scores = study.evaluate(test, (chair, calibrated))
    for new, old in zip(scores, earlier["test_states"], strict=True):
        assert new["arms"]["learned_team"]["question"] == old["arms"]["learned_team"]["question"]
        for intact in ("exact_public_oracle", "probability_product", "learned_chair_exact_reply"):
            assert new["arms"][intact] == old["arms"][intact]
    return {"updates": study.UPDATES, "trace": trace, "responder_weights": calibrated.tolist(),
            "held": study.aggregate(scores), "response_errors": reply_coverage.response_error(test, (chair, calibrated)),
            "sha256": {p.name: study.sha256(p.read_bytes()).hexdigest() for p in (
                file, Path(__file__), HERE / "reply-credit-protocol.md")}}


if __name__ == "__main__":
    E.emit(run())
