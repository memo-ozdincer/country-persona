"""Train the joint controller with paired visible-consistency examples."""
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch

import conflict_roster
import fit_balanced as balanced

fit, E = balanced.fit, balanced.E
HERE = conflict_roster.HERE
EVIDENCE = HERE / "conflict-evidence"


def calibration_data(cases, bank, split):
    features, base = zip(*(fit.encoded(bank, f'{split}/{row["id"]}') for row in cases), strict=True)
    features, base = torch.stack(features), torch.stack(base)
    values = fit.tensor([[1. if action in row["supported"] else -1. for action in fit.env.DECISIONS] for row in cases])
    return features, base, values


def augmented(normal, values, extra):
    h, z, j, y = normal
    features, base, v = extra
    n = len(features)
    added = (torch.zeros((n, h.shape[-1]), dtype=h.dtype), torch.zeros((n, z.shape[-1]), dtype=z.dtype),
             features[:, None, :].expand(-1, 3, -1), base[:, None, :].expand(-1, 3, -1))
    return tuple(torch.cat((a, b)) for a, b in zip(normal, added, strict=True)), torch.cat(
        (values, v[:, None, :].expand(-1, 3, -1)))


def expected_mix(n):
    def expected(players, rewards):
        actor, chair = players
        term = balanced.mix((actor[:n], chair[:n]), rewards[:n])
        extra = (chair[n:, 0] * rewards[n:, 0]).sum(-1)
        return .75 * term.mean() + .25 * extra.mean()
    return expected


def sensitivity(cases, observations, models):
    h, z, v = observations
    rows, totals = {}, {}
    for mode, weights in models.items():
        decisions = (z + h @ weights).argmax(-1)
        rows[mode] = {case["id"]: {
            "label": fit.env.DECISIONS[int(index)], "supported": v[i, index].item() > 0,
            "kind": case["kind"], "correct_options": case["supported"], "endorsed": case["endorsed"]
        } for i, (case, index) in enumerate(zip(cases, decisions, strict=True))}
        results = rows[mode]
        paired = {r["id"].rsplit("/", 1)[0] for r in cases}
        totals[mode] = {
            k: sum(q["supported"] for q in results.values() if q["kind"] == k)
            for k in ("consistent", "contradictory")
        } | {
            "both": sum(results[f"{key}/consistent"]["supported"] and results[f"{key}/contradictory"]["supported"]
                        for key in paired),
            "changed_decision": sum(results[f"{key}/consistent"]["label"] != results[f"{key}/contradictory"]["label"]
                                    for key in paired),
        }
    return {"rows": rows, "totals": totals}


def run():
    torch.set_num_threads(1)
    for name, stamp in E.read(EVIDENCE / "complete.json").items():
        assert fit.digest(EVIDENCE / name) == stamp
    for name, stamp in E.read(fit.EVIDENCE / "complete.json").items():
        assert fit.digest(fit.EVIDENCE / name) == stamp
    prior_path = HERE / "balanced.json"
    prior = E.read(prior_path)
    cases = E.read(fit.HERE / "roster.json")
    alt = E.read(HERE / "conflict-roster.json")
    assert alt == conflict_roster.run()
    base_a, extra_a = [np.load(folder / "features.npz") for folder in (fit.EVIDENCE, EVIDENCE)]
    train = fit.data(cases["train"], base_a, "train")
    train_values = fit.tensor([r["rewards"] for r in cases["train"]])
    paired = calibration_data(alt["train"], extra_a, "train")
    together, rewards = augmented(train, train_values, paired)
    with patch.object(fit, "expected", expected_mix(len(cases["train"]))):
        weights, trace = fit.fit(together, rewards, True)
    prior_weights = tuple(fit.tensor(w) for w in prior["weights"])
    bias = tuple(fit.tensor(w) for w in E.read(fit.HERE / "results.json")["weights"]["bias"])
    models = {"frozen": torch.zeros_like(weights[1]), "balanced": prior_weights[1], "conflict_fit": weights[1]}
    held = cases["held"]
    outputs = fit.evaluate(held, fit.data(held, base_a, "held"), weights, bias)
    for world, row in outputs.items():
        assert row["frozen"] == prior["splits"]["held"]["rows"][world]["frozen"]
    archive = fit.archived(cases["archived"], base_a, weights, bias)
    return {
        "updates": fit.UPDATES, "auxiliary_weight": .25, "trace": trace, "weights": [w.tolist() for w in weights],
        "held_team": {"results": outputs, "scores": fit.groups(outputs, held)},
        "paired_chair": {split: sensitivity(rows, calibration_data(rows, extra_a, split), models)
                         for split, rows in alt.items()},
        "archived": {"rows": archive, "before": prior["archived"]["after"], "after": balanced.previous.metrics(archive)},
        "sha256": {str(p.relative_to(HERE)): fit.digest(p) for p in (
            Path(__file__), EVIDENCE / "features.npz", HERE / "conflict-roster.json", prior_path,
            HERE / "visible-conflict-protocol.md")},
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
