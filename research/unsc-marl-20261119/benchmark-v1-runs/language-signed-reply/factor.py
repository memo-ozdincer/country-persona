"""Separate compatibility estimation from the choice to spend a reply."""
import torch

import fit
import cases

HERE, E = cases.HERE, cases.E
assert fit.HERE == HERE


def logits(x, base, w, fixed_sign=False):
    residual = x @ w
    sign = base[:, 0] - base[:, 1]
    if not fixed_sign:
        sign = sign + residual[:, 0]
    gate = torch.logsumexp(base[:, :2], dim=-1) - base[:, 2] + residual[:, 1]
    p = gate.sigmoid()
    q = sign.sigmoid()
    return torch.stack((p*q, p*(1-q), 1-p), dim=-1), sign, residual


def learn(h, base, u, target, fixed_sign):
    weights = torch.nn.Parameter(torch.zeros((h.shape[-1], 2), dtype=fit.DTYPE))
    opt = torch.optim.Adam((weights,), lr=fit.LR)
    trace = []
    for step in range(fit.STEPS + 1):
        mass, sign, delta = logits(h, base, weights, fixed_sign)
        value = (mass*u).sum(-1).mean()
        verification = torch.nn.functional.binary_cross_entropy_with_logits(sign, target)
        loss = -value + (0. if fixed_sign else .25*verification) + .002*delta.square().mean()
        trace.append({"step": step, "expected_utility": float(value.detach()),
                      "interpretation_errors": int(((sign >= 0) != target.bool()).sum())})
        if step == fit.STEPS:
            break
        opt.zero_grad()
        loss.backward()
        assert torch.isfinite(weights.grad).all()
        opt.step()
    return weights.detach(), trace


def run():
    torch.set_num_threads(1)
    roster, visible, base, utility = fit.observations()
    n = len(roster["train"])
    items = roster["train"] + roster["held"]
    local_truth = torch.tensor([item["truth"] for item in items], dtype=fit.DTYPE)
    prior = E.read(HERE / "results.json")
    scores = {"frozen": base[n:],
              "residual": base[n:] + visible[n:] @ torch.tensor(prior["weights"]["residual"], dtype=fit.DTYPE)}
    weights, trace, signs = {}, {}, {
        "frozen": int(((base[n:, 0] >= base[n:, 1]) != local_truth[n:].bool()).sum())
    }
    for name, fixed in (("trained_sign", False), ("frozen_sign", True)):
        head, trajectory = learn(visible[:n], base[:n], utility[:n], local_truth[:n], fixed)
        p, meaning, _ = logits(visible[n:], base[n:], head, fixed)
        scores[name] = p
        weights[name] = head.tolist()
        trace[name] = trajectory
        signs[name] = int(((meaning >= 0) != local_truth[n:].bool()).sum())
    rows = fit.review(roster["held"], scores)
    for identifier, verdict in rows.items():
        for same in ("frozen", "residual", "exact"):
            assert verdict["arms"][same] == prior["evaluation"]["held"]["rows"][identifier]["arms"][same]
    return {"weights": weights, "training": trace, "held_sign_errors_if_forced": signs,
            "held": fit.aggregate(rows), "rows": rows,
            "sha256": {path.name: fit.digest(path) for path in (
                HERE / "results.json", HERE / "factor.py", HERE / "factor-protocol.md")}}


if __name__ == "__main__":
    E.emit(run())
