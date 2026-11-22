"""Fit a shared disclosure policy from matched team returns."""
from collections import Counter, defaultdict
from itertools import combinations, product
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import receipt_selection as selection
import workshop_transfer as transfer

episode = transfer.episode
SEEDS = {"training": 606929, "development": 456343, "holdout": 831947, "archives": 691093}
FEATURES = (
    "excludes_live_package", "excludes_requested_package", "closes_frontier",
    "at_most_two_remaining", "at_most_three_live", "sender_knows_remaining_acceptance",
    "asker_offered_remaining_package", "excludes_asker_offer", "known_negative_in_request",
    "ordinary_target_available", "multiple_exclusions", "has_time_after_reply",
)
METRICS = ("certificate", "slots", "checks", "queries", "answers", "scope",
           "retries", "retry_signs", "handoffs")


def played(item, terms, recorded, decision, retry):
    observed = []

    def choose(obs):
        observed.append(obs)
        return decision(obs)

    def context():
        return selection.enabled(True, choose)

    with patch.object(selection.reuse, "singleton_enabled", new=context):
        outcome = episode.rollout(item, terms, lambda _: retry, recorded)
    assert len(observed) <= 1
    return observed[0] if observed else None, outcome


def paired(inputs, retry):
    for item, terms, recorded in inputs:
        obs, disclose = played(item, terms, recorded, lambda _: True, retry)
        withheld = disclose
        if obs is not None:
            other_obs, withheld = played(item, terms, recorded, lambda _: False, retry)
            assert obs == other_obs
        left, right = item[0][1]
        yield ("agreement" if left & right else "impasse"), obs, disclose, withheld


def synthetic(split, widths, size, missing):
    seed = SEEDS[split]
    rows, terms = zip(*episode.base.synth.worlds(widths, size, missing, seed), strict=True)
    pruned = transfer.router.routing.refit.drop_returns(rows, seed + 1)
    return {
        condition: list(paired(
            ((item, desc, None) for item, desc in zip(
                episode.transport.delivery(pruned, seed+2, persistence), terms, strict=True)),
            retry,
        ))
        for condition, persistence, retry in (
            ("independent", 0, "immediate"),
            ("persistent", episode.transport.PERSISTENCE, "immediate"),
        )
    }


def indexed(panels):
    totals = defaultdict(lambda: np.zeros((2, 3), dtype=np.int64))
    groups = tuple(product(panels, ("agreement", "impasse")))
    opportunities = Counter()
    for regime, rows in panels.items():
        for case, obs, disclose, withheld in rows:
            if obs is None:
                continue
            a, b = disclose[:3], withheld[:3]
            value = totals[obs, (regime, case)]
            value[0] += a
            value[1] += b
            opportunities[regime, case] += 1
    views = tuple(sorted({obs for obs, _ in totals}))
    delta = np.asarray([[(totals[obs, group][1]-totals[obs, group][0])
                         for group in groups] for obs in views], dtype=np.int64)
    return views, delta, groups, opportunities


def disclose(obs, policy):
    return next((action for action, rule in reversed(policy)
                 if all(obs[i] == condition for i, condition in rule)), True)


def change(dataset, policy):
    views, deltas, _, _ = dataset
    skip = np.asarray([not disclose(obs, policy) for obs in views], dtype=np.int64)
    effect = np.einsum("i,ijk->jk", skip, deltas)
    value = effect @ np.asarray((200, -3, -1))
    return effect[:, 0], int(value.sum()), effect.tolist()


def fit(training, dev):
    indexed_train, indexed_dev = indexed(training), indexed(dev)
    atoms = tuple(product(range(len(FEATURES)), (False, True)))
    rules = ((), *((atom,) for atom in atoms), *(
        (a, b) for a, b in combinations(atoms, 2) if a[0] != b[0]
    ))
    policy, journal = (), []
    start_train = start_dev = 0
    for step in range(3):
        best = None
        tried = Counter()
        for action, rule in product((False, True), rules):
            proposed = (*policy, (action, rule))
            wins, value, train_effect = change(indexed_train, proposed)
            if value <= start_train or min(wins) < 0:
                continue
            tried["training_guard"] += 1
            wins, dev_value, dev_effect = change(indexed_dev, proposed)
            if dev_value < start_dev or min(wins) < 0:
                continue
            tried["development_guard"] += 1
            key = (value, dev_value, -len(rule))
            if best is None or key > best[0]:
                best = key, proposed, train_effect, dev_effect
        journal.append({"step": step, "passing": dict(tried)})
        if best is None:
            break
        (start_train, start_dev, _), policy, train_effect, dev_effect = best
        journal[-1].update(accepted=policy[-1], training_delta=train_effect, development_delta=dev_effect)
    return policy, journal


def score(rows, decision):
    counts, transitions = Counter(), Counter()
    for case, obs, yes, no in rows:
        send = obs is None or decision(obs)
        outcome = yes if send else no
        counts[case, "presentations"] += 1
        counts[case, "scope_decisions"] += obs is not None
        counts[case, "withheld"] += not send
        for key, value in zip(METRICS, outcome, strict=True):
            counts[case, key] += value
        transitions[case, str(yes[0]), str(outcome[0])] += 1
    flatten = transfer.router.sp.flatten
    return {"counts": flatten(counts), "paired_vs_disclose": flatten(transitions)}


def evaluate(panels, policy):
    return {label: {
        "always_disclose": score(rows, lambda _: True),
        "never_disclose": score(rows, lambda _: False),
        "disclose_if_closes_frontier": score(rows, lambda obs: obs[2]),
        "fit": score(rows, lambda obs: disclose(obs, policy)),
    } for label, rows in panels.items()}


def archive(rows):
    item_rows = [item[0] for _, item, *rest in rows]
    results = {"clean": list(paired(((item, terms, receipt)
               for _, item, receipt, *_, terms in rows), "immediate"))}
    for mode, persistence in (("independent", 0), ("persistent", episode.transport.PERSISTENCE)):
        results[mode] = []
        for offset in range(12):
            delivery = episode.transport.delivery(item_rows, SEEDS["archives"]+offset, persistence)
            results[mode].extend(paired(((item, terms, receipt)
                for item, (_, _, receipt, *_, terms) in zip(delivery, rows, strict=True)), "immediate"))
    return results


def run():
    train = synthetic("training", (5, 6), 700, 2)
    dev = synthetic("development", (6,), 600, 3)
    policy, journal = fit(train, dev)
    heldout = synthetic("holdout", (7, 8), 500, 3)
    sources = {
        "venezuela": list(transfer.cases()),
        "myanmar": list(episode.canonical.myanmar(0)),
        "mali": list(episode.canonical.mali(transfer.load(
            transfer.MALI/"evidence/joint-transfer/metrics.json"), 0)),
    }
    return {
        "scope": "Shared local policy chooses whether to disclose verified exclusions when no compatible requested positive is available. Immediate retry and all other decisions are fixed.",
        "seeds": SEEDS, "features": FEATURES, "policy": policy, "fit": journal,
        "guard_groups": indexed(train)[2],
        "training": evaluate(train, policy), "development": evaluate(dev, policy),
        "heldout": evaluate(heldout, policy),
        "un_fit_families": {name: evaluate(archive(rows), policy) for name, rows in sources.items()},
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
