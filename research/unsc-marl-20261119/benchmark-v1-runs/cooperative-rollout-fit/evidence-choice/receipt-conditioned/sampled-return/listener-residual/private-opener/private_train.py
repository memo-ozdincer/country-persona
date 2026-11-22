"""Train documentary source selection with a privately constrained opener."""
import argparse
from hashlib import sha256
from itertools import combinations, product
import json
from pathlib import Path
from statistics import mean
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import represent as features

fit = features.experiment
old, receipt, reform = fit.old, fit.receipt, fit.reform
SEEDS = (7724401, 7724402, 7724403)
MENUS = (2, 2, 2)
CAPS = (1, 1, 1)


def plan():
    paths = (Path(__file__), HERE / "protocol.md", Path(features.__file__),
             HERE.parent / "results.json", Path(fit.__file__),
             Path(receipt.__file__), Path(reform.__file__), Path(old.__file__),
             reform.HERE / "docket.json", old.tribunals.RELEASE / "release.json")
    return {"seeds": list(SEEDS), "menus_per_split": old.TRAIN_N,
            "updates": old.UPDATES, "sha256": {
                str(path.relative_to(old.tribunals.STUDY)): old.DIGEST(path) for path in paths}}


def scenario(local, edges, rate, share, records=None):
    local = [np.asarray(x) for x in local]
    scene = receipt.features(MENUS, CAPS, local, edges, (rate,) * 3, records)
    return scene, features.private_third(scene, local, edges, share, rate), share


def synthetic(seed, varied):
    rng = np.random.default_rng(seed)
    cases = []
    for _ in range(old.TRAIN_N):
        local = rng.integers(0, 8, (3, 2))
        edges = [(i, int(rng.integers(2)), j, int(rng.integers(2)), int(rng.integers(15)))
                 for i, j in combinations(range(3), 2)]
        rate = rng.choice(reform.RATES)
        prior = rng.choice(reform.SHARES)
        cases.append(scenario(local, edges, rate, prior if varied else .5))
    return cases


def train(cases):
    rng = np.random.default_rng(SEEDS[-1])
    observation = np.stack([s["observe"] for s, _, _ in cases])
    masks = np.stack([s["mask_probabilities"].cumsum()[:-1] for s, _, _ in cases])
    rewards = np.stack([s["returns"] for s, _, _ in cases])
    late = np.stack([s["adaptive"] for s, _, _ in cases])
    third = np.stack([features for _, features, _ in cases])
    priors = np.asarray([share for _, _, share in cases])
    indices = np.arange(len(cases))
    weight = np.zeros(len(old.FEATURES))
    trace, digest, baseline = {}, sha256(), 0.
    for step in range(old.UPDATES + 1):
        if step in fit.original.CHECKPOINTS:
            trace[str(step)] = {"weights": weight.tolist(), "running_baseline": baseline}
        if step == old.UPDATES:
            break
        draw = rng.random((4, len(cases)))
        mask = (draw[0, :, None] >= masks).sum(axis=1)
        b = (draw[1] >= priors).astype(int)
        c, grad_c = fit.original.draw(third, weight, draw[2])
        views = observation[indices, b, mask]
        a, grad_a = fit.original.draw(late[indices, views], weight, draw[3])
        score = rewards[indices, b, c, mask, a]
        weight += old.RATE * np.mean((score - baseline)[:, None] * (grad_a + grad_c), axis=0)
        baseline = .9 * baseline + .1 * float(score.mean())
        digest.update(np.column_stack((mask, b, c, views, a, score)).astype("<i4").tobytes())
    return weight, {"checkpoints": trace, "rollouts": len(cases) * old.UPDATES,
                    "trajectory_sha256": digest.hexdigest()}


def evaluate(case, policies):
    scene, third, share = case
    weights = np.asarray([share, 1. - share])[:, None] * scene["mask_probabilities"][None, :]
    obs = scene["observe"]
    returns = scene["returns"]
    b, mask = np.indices(obs.shape)
    outcomes, plans = {}, {}
    for name, w in policies.items():
        last = int(np.argmax(third @ w))
        actions = np.argmax(scene["adaptive"] @ w, axis=-1)
        outcomes[name] = float(np.sum(weights * returns[b, last, mask, actions[obs]]))
        plans[name] = [actions.tolist(), last]
    for name, views in (("content_ceiling", obs), ("arrival_ceiling", (obs > 0).astype(int))):
        value, actions, last = reform.private.optimal(returns, weights, views)
        outcomes[name], plans[name] = value, [actions, last]
    assert max(outcomes.values()) <= outcomes["content_ceiling"] + 1e-9
    return outcomes, plans


def transfer(policies):
    panels = {}
    sources = {name: reform.setup(order)[1:] for name, order in reform.ORDERS.items()}
    for name, counts, caps, local, edges, scorer in old.un_cases():
        if name == "tribunals":
            assert counts == MENUS and caps == CAPS
            records = {actions: [scorer([(a,) for a in actions], mask) for mask in range(8)]
                       for actions in product(range(2), repeat=3)}
            sources["tribunals"] = local, edges, None, records
    assert "tribunals" in sources
    prior_reform = {
        (r["order"], r["delivery"], r["private_prior"]): r["policies"]
        for r in json.loads((fit.HERE.parent / "results.json").read_text())["transfer_rows"]
    }
    for name, (local, edges, _, records) in sources.items():
        rows = []
        for rate, prior in product(reform.RATES, reform.SHARES):
            case = scenario(local, edges, rate, prior, records)
            outcomes, plans = evaluate(case, policies)
            for arm, (actions, c) in plans.items():
                def action(b, mask):
                    if not mask & 2:
                        return actions[0]
                    return actions[1 if arm == "arrival_ceiling" else b+1]
                direct = sum((prior if b == 0 else 1-prior) *
                             rate ** mask.bit_count() * (1-rate) ** (3-mask.bit_count()) *
                             records[action(b, mask), b, c][mask]
                             for b, mask in product(range(2), range(8)))
                outcomes[arm] += records[0, 0, 0][0]
                assert abs(direct - outcomes[arm]) < 1e-9
            if name in reform.ORDERS:
                archived = prior_reform[name, rate, prior]
                for key, ref in (("public_inventory_fit", "sampled_content"), ("fixed", "fixed_content"),
                                 ("content_ceiling", "content_ceiling")):
                    assert abs(outcomes[key] - archived[ref]["released"]) < 1e-9
            rows.append({"delivery": rate, "prior": prior, "scores": outcomes, "actions": plans})
        panels[name] = rows
    return panels


def summary(rows):
    return {arm: {
        "mean": mean(row[arm] for row in rows),
        "ties_ceiling": sum(abs(row[arm]-row["content_ceiling"]) < 1e-9 for row in rows),
        "wins_vs_fixed": sum(row[arm] > row["fixed"]+1e-9 for row in rows),
        "losses_vs_fixed": sum(row[arm] < row["fixed"]-1e-9 for row in rows),
    } for arm in rows[0]}


def run():
    lock = HERE / "plan.json"
    assert json.loads(lock.read_text()) == plan()
    fair, fair_trace = train(synthetic(SEEDS[0], False))
    varied, varied_trace = train(synthetic(SEEDS[0], True))
    control = json.loads((fit.HERE / "results.json").read_text())
    public = np.asarray(control["control_trace"]["checkpoints"]["150"]["weights"])
    policies = {"fair_prior_fit": fair, "varied_prior_fit": varied,
                "public_inventory_fit": public, "fixed": fit.FIXED}
    held = {}
    for name, varying in (("fair", False), ("varied", True)):
        rows = [evaluate(case, policies)[0] for case in synthetic(SEEDS[1], varying)]
        held[name] = {"summary": summary(rows), "rows": rows}
    historical = transfer(policies)
    return {"plan_sha256": old.DIGEST(lock), "training": {"fair": fair_trace, "varied": varied_trace},
            "held": held, "transfer": {name: {"summary": summary([r["scores"] for r in rows]), "rows": rows}
                                       for name, rows in historical.items()}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run"))
    print(json.dumps({"plan": plan, "run": run}[parser.parse_args().mode](), indent=2))
