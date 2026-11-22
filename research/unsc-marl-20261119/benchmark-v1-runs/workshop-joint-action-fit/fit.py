"""Optimize the two actors' language-conditioned policies by exact shared return."""
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import torch

import environment as env

HERE = env.HERE
EVIDENCE = HERE / "evidence"
UPDATES = 64
LEARNING_RATE = .10
DTYPE = torch.float64


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def tensor(values):
    return torch.as_tensor(np.asarray(values), dtype=DTYPE)


def encoded(files, route):
    h, z = [tensor(files[route + "/" + key]) for key in ("hidden", "logits")]
    return torch.nn.functional.normalize(h, dim=-1), z


def data(rows, files, split):
    responder_h, responder_z, chair_h, chair_z = [], [], [], []
    for row in rows:
        prefix = f'{split}/{row["id"]}'
        h, z = encoded(files, prefix + "/responder")
        responder_h.append(h)
        responder_z.append(z)
        branches = [encoded(files, prefix + "/" + a) for a in env.RESPONSES]
        h, z = [torch.stack(items) for items in zip(*branches, strict=True)]
        chair_h.append(h)
        chair_z.append(z)
    return tuple(torch.stack(xs) for xs in (responder_h, responder_z, chair_h, chair_z))


def response_and_chair(inputs, weights):
    h, z, j, y = inputs
    return (z + h @ weights[0]).softmax(-1), (y + j @ weights[1]).softmax(-1)


def expected(actors, rewards):
    p, q = actors
    return (p * (q * rewards).sum(-1)).sum(-1)


def fit(inputs, rewards, use_features):
    h, z, j, y = inputs
    if not use_features:
        h, j = torch.ones_like(h[..., :1]), torch.ones_like(j[..., :1])
    features = (h, z, j, y)
    parameters = [torch.nn.Parameter(torch.zeros((h.shape[-1], z.shape[-1]), dtype=DTYPE)),
                  torch.nn.Parameter(torch.zeros((j.shape[-1], y.shape[-1]), dtype=DTYPE))]
    opt = torch.optim.Adam(parameters, lr=LEARNING_RATE)
    trace = []
    for step in range(UPDATES + 1):
        policies = response_and_chair(features, parameters)
        score = expected(policies, rewards).mean()
        delta = (h @ parameters[0]).square().mean() + (j @ parameters[1]).square().mean()
        trace.append({"step": step, "return": float(score.detach()), "mean_squared_residual": float(delta.detach())})
        if step == UPDATES:
            break
        opt.zero_grad()
        (-score + .002 * delta).backward()
        assert all(torch.isfinite(p.grad).all() for p in parameters)
        trace[-1]["gradient_norms"] = [float(p.grad.norm()) for p in parameters]
        opt.step()
    return tuple(p.detach() for p in parameters), trace


def variants(inputs, weights, biases):
    h, z, j, y = inputs
    frozen = z.softmax(-1), y.softmax(-1)
    fitted = response_and_chair(inputs, weights)
    bias = response_and_chair((torch.ones_like(h[..., :1]), z, torch.ones_like(j[..., :1]), y), biases)
    fixed = torch.zeros_like(z)
    fixed[:, 0] = 1.
    return {"frozen": frozen, "joint": fitted, "bias_only": bias, "only_responder_changed": (fitted[0], frozen[1]),
            "only_chair_changed": (frozen[0], fitted[1]), "always_disclose_frozen_chair": (fixed, frozen[1]),
            "always_disclose_fitted_chair": (fixed, fitted[1])}


def evaluate(frozen_worlds, inputs, weights, biases):
    values = tensor([row["rewards"] for row in frozen_worlds])
    output = {row["id"]: {} for row in frozen_worlds}
    for name, policies in variants(inputs, weights, biases).items():
        picked = policies[0].argmax(-1)
        advised = policies[1].argmax(-1)
        means = expected(policies, values)
        for i, row in enumerate(frozen_worlds):
            r = int(picked[i])
            m = int(advised[i, r])
            label = env.DECISIONS[m]
            support = label in row["certifiable"][r]
            output[row["id"]][name] = {
                "response": env.RESPONSES[r], "chair": label, "chair_after_each_response": [env.DECISIONS[k] for k in advised[i]],
                "truthful": not (r == 1 and not row["proposal_compatible"]),
                "supported": support, "supported_correct": support and label in row["gold"],
                "expected_return": float(means[i]), "greedy_return": float(values[i, r, m]),
            }
    for i, row in enumerate(frozen_worlds):
        oracle_choice = min(row["gold"])
        output[row["id"]]["exact_with_disclosure"] = {
            "response": "K", "chair": oracle_choice, "truthful": True,
            "supported": True, "supported_correct": True,
            "greedy_return": float(values[i, 0, env.DECISIONS.index(oracle_choice)]),
            "expected_return": float(values[i, 0, env.DECISIONS.index(oracle_choice)]),
        }
    return output


def groups(results, cases):
    summary = {}
    for group in ("all", *sorted({r["id"].split("-")[0] for r in cases} - {"synthetic"})):
        selected = [row for key, row in results.items() if group == "all" or key.startswith(group + "-")]
        summary[group] = {}
        for mode in selected[0]:
            scores = [r[mode] for r in selected]
            summary[group][mode] = {"n": len(scores), "commits": sum(r["supported_correct"] for r in scores),
                                    "truthful": sum(r["truthful"] for r in scores),
                                    "supported": sum(r["supported"] for r in scores),
                                    "greedy_return": sum(r["greedy_return"] for r in scores) / len(scores),
                                    "expected_return": sum(r["expected_return"] for r in scores) / len(scores)}
    return summary


def archived(rows, features, model, bias):
    result = {}
    for row in rows:
        h, logits = encoded(features, f'archived/{row["id"]}/archived')
        scores = {"frozen": logits, "joint_chair": logits + h @ model[1], "bias_only": logits + bias[1][0]}
        result[row["id"]] = {"supported": row["supported"], "gold": row["gold"], "arms": {}}
        for key, vector in scores.items():
            a = env.DECISIONS[int(vector.argmax())]
            result[row["id"]]["arms"][key] = {"decision": a, "evidence_supported": a in row["supported"],
                                              "gold_correct": a in row["gold"]}
    return result


def run():
    torch.set_num_threads(1)
    assert all(digest(EVIDENCE / file) == stamp for file, stamp in env.E.read(EVIDENCE / "complete.json").items())
    roster = env.E.read(HERE / "roster.json")
    assert roster == env.roster()
    features = np.load(EVIDENCE / "features.npz")
    d = data(roster["train"], features, "train")
    rewards = tensor([r["rewards"] for r in roster["train"]])
    model, trace = fit(d, rewards, True)
    bias, bias_trace = fit(d, rewards, False)
    output = {}
    for split in ("train", "held"):
        cases = roster[split]
        results = evaluate(cases, data(cases, features, split), model, bias)
        output[split] = {"rows": results, "aggregate": groups(results, cases)}
    return {
        "updates_per_fit": UPDATES, "learning_rate": LEARNING_RATE, "frozen_qwen_updates": 0,
        "train_trace": trace, "bias_trace": bias_trace,
        "weights": {"residual": [a.tolist() for a in model], "bias": [a.tolist() for a in bias]},
        "synthetic_and_v1": output, "archived_transcripts_chair_only": archived(roster["archived"], features, model, bias),
        "sha256": {p.name: digest(p) for p in (HERE / "roster.json", Path(__file__), EVIDENCE / "features.npz")},
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
