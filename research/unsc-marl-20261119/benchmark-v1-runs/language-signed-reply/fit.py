"""Learn a signed-response head from exact local counterfactual team rewards."""
from hashlib import sha256
from pathlib import Path

import numpy as np
import torch

import cases

HERE, E = cases.HERE, cases.E
CAPTURE = HERE / "evidence"
STEPS = 96
LR = .12
DTYPE = torch.float64


def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def observations():
    d = np.load(CAPTURE / "vectors.npz")
    h = torch.nn.functional.normalize(torch.from_numpy(d["hidden"]).to(DTYPE), dim=-1)
    z = torch.from_numpy(d["logits"]).to(DTYPE)
    roster = cases.roster()
    rows = [r for split in roster.values() for r in split]
    assert len(rows) == len(h) == len(z)
    u = torch.tensor([r["utility"] for r in rows], dtype=DTYPE)
    return roster, h, z, u


def train(x, base, u, objective=None):
    w = torch.nn.Parameter(torch.zeros((x.shape[-1], len(cases.DEC)), dtype=DTYPE))
    optimizer = torch.optim.Adam([w], lr=LR)
    trace = []
    for step in range(STEPS + 1):
        residual = x @ w
        scores = base + residual
        p = scores.softmax(-1)
        utility = (p * u).sum(-1).mean()
        loss = -utility if objective is None else objective(scores, u)
        trace.append({"step": step, "return": float(utility.detach()), "loss": float(loss.detach())})
        if step == STEPS:
            break
        optimizer.zero_grad()
        (loss + .002 * residual.square().mean()).backward()
        assert torch.isfinite(w.grad).all()
        optimizer.step()
    return w.detach(), trace


def review(rows, tensor_logits):
    outcomes = {}
    for k, row in enumerate(rows):
        verdict = {}
        exact = cases.DEC[int(np.argmax(row["utility"]))]
        for name, logits in tensor_logits.items():
            selected = cases.DEC[int(logits[k].argmax())]
            audit = row["audit"][selected]
            verdict[name] = {"selected": selected, **audit,
                             "best_response": selected == exact,
                             "missed_proof": selected == "P" and exact != "P",
                             "avoidable_send": selected != "P" and audit["truthful"] and exact == "P",
                             "net": row["utility"][cases.DEC.index(selected)]}
        signed = "Y" if row["truth"] else "N"
        for name, value in (("truthful_always_send", signed), ("exact", exact)):
            audit = row["audit"][value]
            verdict[name] = {"selected": value, **audit, "best_response": value == exact, "missed_proof": False,
                             "avoidable_send": value != "P" and exact == "P",
                             "net": row["utility"][cases.DEC.index(value)]}
        outcomes[row["id"]] = {"family": row["family"], "mode": row["mode"], "role": row["role"],
                                "gold": row["gold"], "queried": row["target"], "arms": verdict}
    return outcomes


def aggregate(outcomes):
    controls = list(next(iter(outcomes.values()))["arms"])
    families = {r["family"] for r in outcomes.values()}
    selected = {"all": list(outcomes.values())}
    for field, labels in (("family", sorted(families)), ("mode", ("two_openings", "last_unknown", "certified"))):
        for key in labels:
            selected[key] = [r for r in outcomes.values() if r[field] == key]
    rows = {}
    for key, outcomes in selected.items():
        rows[key] = {}
        for arm in controls:
            results = [r["arms"][arm] for r in outcomes]
            rows[key][arm] = {
                "n": len(results), "false_sign": sum(not v["truthful"] for v in results),
                "wrong_commit_if_delivered": sum(v["wrong_commit"] for v in results),
                "certifying_true_reply_if_delivered": sum(v["new_proof"] for v in results),
                "best_response": sum(v["best_response"] for v in results),
                "missed_proof": sum(v["missed_proof"] for v in results),
                "avoidable_send": sum(v["avoidable_send"] for v in results),
                "mean_net": sum(v["net"] for v in results)/len(results),
            }
    return rows


def run():
    torch.set_num_threads(1)
    assert all(digest(CAPTURE / f) == stamp for f, stamp in E.read(CAPTURE / "complete.json").items())
    roster, h, z, u = observations()
    n = len(roster["train"])
    bias_x = torch.ones_like(h[:, :1])
    complete, history = train(h[:n], z[:n], u[:n])
    bias, bias_trace = train(bias_x[:n], z[:n], u[:n])
    logits = {"frozen": z, "bias_only": z + bias_x @ bias, "residual": z + h @ complete}
    evaluation = {}
    for split, index in (("train", slice(0, n)), ("held", slice(n, None))):
        details = review(roster[split], {name: data[index] for name, data in logits.items()})
        evaluation[split] = {"rows": details, "summary": aggregate(details)}
    return {"updates_per_fit": STEPS, "backbone_updates": 0, "trajectories": {"residual": history, "bias_only": bias_trace},
            "weights": {"residual": complete.tolist(), "bias": bias.tolist()},
            "evaluation": evaluation, "sha256": {p.name: digest(p) for p in (Path(__file__), HERE / "roster.json",
            CAPTURE / "vectors.npz", HERE / "protocol.md")}}


if __name__ == "__main__":
    E.emit(run())
