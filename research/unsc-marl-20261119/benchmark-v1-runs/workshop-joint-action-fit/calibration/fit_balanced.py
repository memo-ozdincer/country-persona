"""Keep incomplete and complete evidence in the chair's training mix."""
from collections import Counter
from pathlib import Path
import sys
from unittest.mock import patch

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import disclosure_mixture as previous
import fit

E = fit.env.E
ORIGINAL_EXPECTED = fit.expected


def mix(policies, rewards):
    actor, chair = policies
    forced = torch.zeros_like(actor)
    forced[:, 0] = .25
    forced[:, 2] = .25
    return ORIGINAL_EXPECTED((.5 * actor + forced, chair), rewards)


def branch_checks(worlds, world_rows):
    output = {}
    for policy in ("frozen", "joint", "bias_only"):
        rows = [(r, world_rows[r["id"]][policy]) for r in worlds]
        output[policy] = {}
        for branch, name in enumerate(fit.env.RESPONSES):
            decisions = [p["chair_after_each_response"][branch] for _, p in rows]
            output[policy][name] = {
                "support": sum(decision in r["certifiable"][branch] for (r, _), decision in zip(rows, decisions, strict=True)),
                "labels": dict(Counter(decisions)),
            }
    return output


def run():
    torch.set_num_threads(1)
    for file, digest in E.read(fit.EVIDENCE / "complete.json").items():
        assert fit.digest(fit.EVIDENCE / file) == digest
    roster_path = HERE.parent / "roster.json"
    roster = E.read(roster_path)
    assert roster == fit.env.roster()
    source_path = HERE.parent / "disclosure-mixture.json"
    complete_mixture = E.read(source_path)
    old = E.read(HERE.parent / "results.json")
    features = np.load(fit.EVIDENCE / "features.npz")
    dev = roster["train"]
    train = fit.data(dev, features, "train")
    values = fit.tensor([row["rewards"] for row in dev])
    false_rows = torch.tensor([not row["proposal_compatible"] for row in dev])
    assert false_rows.any() and (values[false_rows, 1].amax(-1) == values[false_rows, 1].amin(-1)).all()
    with patch.object(fit, "expected", mix):
        weights, trace = fit.fit(train, values, True)
    bias = tuple(fit.tensor(a) for a in old["weights"]["bias"])
    splits = {}
    for key in ("train", "held"):
        rows = roster[key]
        data = fit.data(rows, features, key)
        result = fit.evaluate(rows, data, weights, bias)
        earlier = complete_mixture["evaluation"][key]["rows"]
        for world, row in result.items():
            for same in ("frozen", "bias_only", "exact_with_disclosure"):
                assert earlier[world][same] == row[same]
        splits[key] = {"scores": fit.groups(result, rows), "rows": result,
                       "branch_checks": branch_checks(rows, result),
                       "prior_branch_checks": branch_checks(rows, earlier)}
    archive = fit.archived(roster["archived"], features, weights, bias)
    return {
        "forced_training_mass": {"K": .25, "W": .25}, "trace": trace,
        "false_endorsement_worlds_constant_chair_reward": int(false_rows.sum()),
        "weights": [w.tolist() for w in weights], "splits": splits,
        "archived": {"actions": archive, "before": complete_mixture["archived"]["after"],
                     "after": previous.metrics(archive)},
        "sha256": {str(path.relative_to(HERE.parent)): fit.digest(path)
                   for path in (Path(__file__), HERE / "protocol.md", roster_path, source_path,
                                fit.EVIDENCE / "features.npz")},
    }


if __name__ == "__main__":
    E.emit(run())
