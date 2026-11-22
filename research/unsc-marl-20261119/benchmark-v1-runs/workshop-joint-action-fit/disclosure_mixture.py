"""Replay the exact expected update with a half-disclosure training mixture."""
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch

import fit

HERE = fit.HERE
ORIGINAL_EXPECTED = fit.expected


def mixture(policies, rewards):
    actor, chair = policies
    fixed = torch.zeros_like(actor)
    fixed[:, 0] = 1.
    return ORIGINAL_EXPECTED(((actor + fixed) / 2, chair), rewards)


def metrics(rows):
    return {
        name: {"supported": sum(row["arms"][name]["evidence_supported"] for row in rows.values()),
               "gold": sum(row["arms"][name]["gold_correct"] for row in rows.values())}
        for name in next(iter(rows.values()))["arms"]
    }


def run():
    torch.set_num_threads(1)
    cases = fit.env.E.read(HERE / "roster.json")
    original_path = HERE / "results.json"
    former = fit.env.E.read(original_path)
    features = np.load(fit.EVIDENCE / "features.npz")
    train = fit.data(cases["train"], features, "train")
    reward = fit.tensor([row["rewards"] for row in cases["train"]])
    with patch.object(fit, "expected", mixture):
        model, trace = fit.fit(train, reward, True)
    bias = tuple(fit.tensor(m) for m in former["weights"]["bias"])
    results = {}
    for split in ("train", "held"):
        rows = cases[split]
        results[split] = fit.evaluate(rows, fit.data(rows, features, split), model, bias)
        for key, arm in results[split].items():
            for unchanged in ("frozen", "bias_only", "exact_with_disclosure"):
                assert arm[unchanged] == former["synthetic_and_v1"][split]["rows"][key][unchanged]
    archived = fit.archived(cases["archived"], features, model, bias)
    return {"updates": fit.UPDATES, "forced_disclosure_mass_in_training": 0.5,
            "trace": trace, "weights": [w.tolist() for w in model],
            "evaluation": {split: {"rows": results[split], "aggregate": fit.groups(results[split], cases[split])}
                           for split in results},
            "archived": {"actions": archived, "before": metrics(former["archived_transcripts_chair_only"]),
                         "after": metrics(archived)},
            "sha256": {p.name: fit.digest(p) for p in (original_path, Path(__file__), HERE / "disclosure-mixture-protocol.md")}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
