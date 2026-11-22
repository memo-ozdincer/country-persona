"""Test the effect of separating partner-specific evidence links."""
import argparse
from itertools import combinations
import json
from pathlib import Path

import numpy as np

import private_train as prior


HERE = Path(__file__).resolve().parent


def menus(seed, split):
    rng = np.random.default_rng(seed)
    results, collisions = [], []
    for _ in range(prior.old.TRAIN_N):
        local = rng.integers(0, 8, (3, 2))
        links = [(i, int(rng.integers(2)), j, int(rng.integers(2)), int(rng.integers(15)))
                 for i, j in combinations(range(3), 2)]
        used, edges, changed = {}, [], 0
        for i, a, j, b, score in links:
            selected = []
            for desk, card in ((i, a), (j, b)):
                collision = desk in used and used[desk] == card
                changed += collision
                chosen = 1 - card if split and collision else card
                used[desk] = chosen
                selected.append(chosen)
            edges.append((i, selected[0], j, selected[1], score))
        rate = rng.choice(prior.reform.RATES)
        share = rng.choice(prior.reform.SHARES)
        results.append(prior.scenario(local, edges, rate, share))
        collisions.append(changed)
    return results, collisions


def plan():
    paths = (Path(__file__), HERE / "split-protocol.md", HERE / "plan.json",
             HERE / "results.json", Path(prior.__file__))
    return {"sha256": {p.name: prior.old.DIGEST(p) for p in paths}, "seeds": list(prior.SEEDS)}


def run():
    assert json.loads((HERE / "split-plan.json").read_text()) == plan()
    saved = json.loads((HERE / "results.json").read_text())
    train, counts = menus(prior.SEEDS[0], True)
    fitted, trace = prior.train(train)
    assert trace["rollouts"] == saved["training"]["varied"]["rollouts"]
    old = np.asarray(saved["training"]["varied"]["checkpoints"]["150"]["weights"])
    control = json.loads((prior.fit.HERE / "results.json").read_text())
    public = np.asarray(control["control_trace"]["checkpoints"]["150"]["weights"])
    # The transfer helper verifies the public-inventory and fixed results against the archive.
    policies = {"split_fit": fitted, "varied_prior_fit": old, "public_inventory_fit": public,
                "fixed": prior.fit.FIXED}
    held = {}
    for name, split in (("unrestricted", False), ("separate_relations", True)):
        cases, collisions = menus(prior.SEEDS[1], split)
        rows = [prior.evaluate(case, policies)[0] for case in cases]
        if not split:
            for current, archived in zip(rows, saved["held"]["varied"]["rows"], strict=True):
                assert all(current[k] == archived[k] for k in current if k != "split_fit")
        held[name] = {"original_collisions_per_menu": collisions, "summary": prior.summary(rows), "rows": rows}
    archival = prior.transfer(policies)
    return {"lock_sha256": prior.old.DIGEST(HERE / "split-plan.json"), "trace": trace,
            "training_original_collisions": counts, "held": held,
            "transfer": {key: {"summary": prior.summary([r["scores"] for r in rows]), "rows": rows}
                         for key, rows in archival.items()}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run"))
    print(json.dumps({"plan": plan, "run": run}[parser.parse_args().mode](), indent=2))
