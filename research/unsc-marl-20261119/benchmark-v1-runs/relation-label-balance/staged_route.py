"""Separate responder policy updates from upstream exploration."""
import argparse
from collections import Counter
from pathlib import Path
from statistics import mean

import numpy as np

import learn_route as prior

HERE, team = prior.HERE, prior.team


def plan():
    files = (Path(__file__), HERE / "staged-protocol.md", Path(prior.__file__),
             HERE / "route-results.json", HERE / "verified.json", HERE / "results.json",
             prior.study.OUT / "calls.jsonl")
    return {"input_sha256": {str(p.relative_to(team.STUDY)): team.pin(p) for p in files},
            "updates_per_head": prior.STEPS, "step": prior.RATE,
            "penalty": prior.L2, "query_cost": prior.COST}


def family_weight(rows):
    counts = Counter(r["family"] for r in rows)
    return [1 / (len(counts) * counts[row["family"]]) for row in rows]


def receiver(row, w):
    return prior.softmax(row["z"] @ w, row["legal"])


def update(w, objective):
    before, gradient = objective(w)
    for ix in np.ndindex(w.shape):
        up, down = w.copy(), w.copy()
        up[ix] += 1e-5
        down[ix] -= 1e-5
        numeric = (objective(up)[0] - objective(down)[0]) / 2e-5
        assert abs(numeric - gradient[ix]) < 1e-8
    for _ in range(prior.STEPS):
        _, gradient = objective(w)
        w += prior.RATE * gradient
    after, _ = objective(w)
    assert after >= before and np.isfinite(w).all()
    return w, [before, after]


def staged(train):
    mass = family_weight(train)
    def reviewer(w):
        value = 0.
        gradient = np.zeros_like(w)
        for row, weight in zip(train, mass, strict=True):
            p = receiver(row, w)
            returns = row["reply_rewards"]
            mean_return = (p * returns).sum(axis=-1)
            value += weight * float(mean_return.mean())
            gradient += weight * row["z"].T @ (p * (returns - mean_return[:, None])) / 2
        return value, gradient - prior.L2 * w
    review, trace_receiver = update(np.zeros((6, 3)), reviewer)
    branches = []
    for row in train:
        choices = receiver(row, review).argmax(axis=1)
        returns = row["reply_rewards"][np.arange(2), choices]
        branches.append(np.r_[row["opening"], returns - prior.COST])

    def proposer(w):
        value = 0.
        gradient = np.zeros_like(w)
        for row, weight, returns in zip(train, mass, branches, strict=True):
            p = prior.softmax(row["x"] @ w, [True, row["first"] != 2, True, True])
            expected = float(p @ returns)
            value += weight * expected
            gradient += weight * np.outer(row["x"], p * (returns - expected))
        return value, gradient - prior.L2 * w
    propose, trace_proposer = update(np.zeros((4, 4)), proposer)
    return (propose, review), {"reviewer_both_views": trace_receiver, "proposer_live_branches": trace_proposer}


def readout(row, weights):
    p, q = prior.strategies(row, weights)
    replies = q.argmax(axis=1)
    outcomes = [prior.stats(row, a, int(replies[a-2]) if a >= 2 else 0) for a in range(4)]
    choice = int(p.argmax())
    value, checks, label = outcomes[choice]
    return {"net": value, "checks": checks, "relation": team.LABELS[label],
            "sampled_proposal_net": float(p @ [v for v, _, _ in outcomes]),
            "sampled_proposal_checks": float(p[2:].sum()), "proposal_action": choice,
            "reviewer_routes": replies.tolist(), "proposal_probabilities": p.tolist()}


def trial(train, test, baseline):
    weights, traces = staged(train)
    prior_weights = tuple(np.asarray(w) for w in baseline["weights"])
    assert baseline["fit_families"] == sorted({r["family"] for r in train})
    outcomes = {}
    original = {r["case"]:r for r in baseline["results"]}
    for row in test:
        key = row["key"]
        variants = {
            "staged": weights,
            "staged_proposer_joint_reviewer": (weights[0], prior_weights[1]),
            "joint_proposer_staged_reviewer": (prior_weights[0], weights[1]),
            "joint": prior_weights,
        }
        policies = {k: readout(row, w) for k, w in variants.items()}
        previous = original[key]["policy"]
        assert all(policies["joint"][k] == previous["learned"][k] for k in ("net", "checks", "relation"))
        for name in ("first_only", "fixed_train", "always_0_agreement", "always_1_second", "cycles_unanimous_three"):
            policies[name] = previous[name]
        outcomes[key] = {"truth": team.LABELS[row["gold"]], "policies": policies}
    metrics = {}
    for name in next(iter(outcomes.values()))["policies"]:
        rows = [row["policies"][name] for row in outcomes.values()]
        metrics[name] = {
            "net": mean(r["net"] for r in rows),
            "checks": mean(r["checks"] for r in rows),
            "correct": sum(row["policies"][name]["relation"] == row["truth"] for row in outcomes.values()),
            "decisive_errors": sum(row["policies"][name]["relation"] not in (row["truth"], "unknown")
                                  for row in outcomes.values()),
        }
    return {"training_families": baseline["fit_families"], "weights": [w.tolist() for w in weights],
            "objective": traces, "outcomes": outcomes, "means": metrics,
            "staged_sampled_proposal_net": mean(r["policies"]["staged"]["sampled_proposal_net"]
                                               for r in outcomes.values())}


def run():
    assert plan() == team.read(HERE / "staged-plan.json")
    assert prior.study.e.json.loads(prior.study.e.json.dumps(prior.run())) == team.read(HERE / "route-results.json")
    results = team.read(HERE / "route-results.json")
    rows = prior.load()
    archive = [r for r in rows if r["family"] != "myanmar"]
    groups = {name: trial([r for r in archive if r["family"] != name],
                          [r for r in archive if r["family"] == name], data)
              for name, data in results["folds"].items()}
    assert all(name not in value["training_families"] for name, value in groups.items())
    aggregate = {arm: {k: mean(r["means"][arm][k] for r in groups.values()) for k in ("net", "checks")}
                 for arm in next(iter(groups.values()))["means"]}
    return {"folds":groups, "archive_macro":aggregate,
            "myanmar":trial(archive, [r for r in rows if r["family"] == "myanmar"], results["myanmar"]),
            "plan_sha256":team.pin(HERE / "staged-plan.json")}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("plan", "run"))
    prior.study.e.emit({"plan":plan,"run":run}[p.parse_args().mode]())
