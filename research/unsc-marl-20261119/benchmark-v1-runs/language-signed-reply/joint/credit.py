"""Fit direct send and question values on the same role-local signatures."""
from pathlib import Path

import torch

import train_team as study

E, HERE = study.E, study.HERE


def train_reply(batch):
    eligible, _, h, base, delta, _ = batch
    value = delta[eligible]
    x, initial = h[eligible], base[eligible]
    target = value.gt(0).to(study.DTYPE)
    prevalence = target.mean()
    weights = .5 * (target/prevalence + (1-target)/(1-prevalence))
    r = torch.nn.Parameter(torch.zeros(h.shape[-1], dtype=study.DTYPE))
    optimizer = torch.optim.Adam([r], lr=.12)
    trace = []
    for step in range(study.UPDATES+1):
        adjustment = x @ r
        probability = initial + adjustment
        loss = (weights * torch.nn.functional.binary_cross_entropy_with_logits(
            probability, target, reduction="none")).mean()
        trace.append({"step": step, "loss": float(loss.detach()),
                      "wrong_send_choice": int((probability.gt(0) != target.bool()).sum())})
        if step == study.UPDATES:
            break
        optimizer.zero_grad()
        (loss + .002 * adjustment.square().mean()).backward()
        assert torch.isfinite(r.grad).all()
        optimizer.step()
    return r.detach(), trace


def learn_chair(batch, reply):
    visible, features, h, base, delta, _ = batch
    send = (base + h @ reply).gt(0)
    values = delta * send - study.QUERY_COST
    # The counterfactual answer influences the training target, never the feature.
    x, y = features[visible], values[visible].unsqueeze(1)
    solution = torch.linalg.lstsq(x, y, driver="gelsd")
    prediction = x @ solution.solution
    return solution.solution[:,0], {"rank": int(solution.rank), "label_count": len(x),
                                    "rmse": float((prediction-y).square().mean().sqrt())}


def run():
    torch.set_num_threads(1)
    original_path = HERE / "results.json"
    original = E.read(original_path)
    roster, hidden, frozen, _ = study.reply_fit.observations()
    n = len(roster["train"])
    train = study.replay_rows(roster["train"], False)
    held = study.replay_rows(roster["held"], True)
    environment = study.prepare(train, hidden[:n], frozen[:n])
    evaluation = study.prepare(held, hidden[n:], frozen[n:])
    reply, history = train_reply(environment)
    chair, regression = learn_chair(environment, reply)
    old_c, old_r = (torch.tensor(w, dtype=study.DTYPE) for w in original["weights"])
    empirical = study.prior_map(train)
    systems = {"both_direct": (chair, reply), "direct_chair_only": (chair, old_r),
               "direct_reply_only": (old_c, reply)}
    policies = {}
    replay = {}
    for name, pair in systems.items():
        output = study.evaluate(held, evaluation, pair, empirical)
        for item, baseline in zip(output, original["held"], strict=True):
            for control in ("silence", "delivery_exact_reply", "public_value_exact_reply", "private_world_ceiling"):
                assert item["arms"][control] == baseline["arms"][control]
        policies[name] = study.summary(output)
        replay[name] = {item["key"] + "/" + str(j % len(study.HELD_RATES)): item["arms"]["learned_team"]
                        for j, item in enumerate(output)}
        assert len(replay[name]) == len(output)
    return {"training": {"reply": history, "chair": regression}, "weights": [chair.tolist(), reply.tolist()],
            "systems": policies, "held_actions": replay,
            "sha256": {p.name: study.reply_fit.digest(p) for p in (
                original_path, Path(__file__), HERE / "credit-protocol.md")}}


if __name__ == "__main__":
    E.emit(run())
