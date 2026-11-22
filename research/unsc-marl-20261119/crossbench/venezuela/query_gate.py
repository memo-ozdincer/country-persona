"""Learn whether to spend the one query from bounded decentralized state."""
from collections import Counter, defaultdict
from itertools import combinations, product
import json
from unittest.mock import patch

import numpy as np

import noisy_frontier as frontier

episode, router = frontier.episode, frontier.router
transfer, selection = frontier.transfer, frontier.selection
FEATURES = (
    "few_live", "several_known_exclusions", "covers_all_but_one", "other_offer_ruled_out",
    "other_offer_unknown", "request_contains_own_offer", "only_one_known_live_acceptance",
    "several_live_unknown", "other_receipt_cached", "at_least_four_slots",
    "ordinary_would_check",
)
SEEDS = {"training": 339761, "validation": 905671, "holdout": 879661}
METRICS = ("certificate", "slots", "checks", "queries", "answers", "scope_queries")


def local_view(item, state, moves, regular):
    public, actor, slot, credit = state
    peer = 1-actor
    width = item[0][0]
    yes, no = item[0][2][actor]
    full = (1 << width)-1
    live = full & ~(public[1] | public[3])
    target_set = moves[selection.group.OFFER_SET]
    peer_offer = public[peer*2] & live
    return (
        live.bit_count() <= 3, (live&no).bit_count() >= 2,
        (live&~no).bit_count() <= 1, bool(peer_offer&no), bool(peer_offer&~(yes|no)),
        bool(target_set&public[actor*2]), (yes&live).bit_count() <= 1,
        (live&~(yes|no)).bit_count() >= 2, bool(credit&(selection.reuse.CACHE<<peer)),
        width+1-slot >= 4, regular[2][0] == episode.delay.CHECK,
    )


def traced(item, terms, receipt, decide):
    def setup():
        return selection.enabled(True, frontier.ordinary_when_possible)

    observed = []
    with patch.object(selection.reuse, "singleton_enabled", new=setup):
        with transfer.canonical.enabled(terms, "public", lambda: episode.delay.enabled(
                lambda _: "immediate")):
            available = router.available
            default = router.default

            def view(item, state):
                obs, moves, routine = available(item, state)
                extra = None
                if default(obs, transfer.canonical.BASE) == selection.group.OFFER_SET:
                    extra = local_view(item, state, moves, routine)
                return (*obs, extra), moves, routine

            def action(obs, mode):
                fixed = default(obs[:-1], mode)
                if mode == "never":
                    return fixed
                if obs[-1] is not None and not observed:
                    observed.append((obs[-1], decide(obs[-1])))
                if observed and not observed[0][1]:
                    return selection.reuse.ROUTER.ROUTINE
                return fixed

            with patch.object(router, "available", new=view), patch.object(router, "default", new=action):
                result = router.play(item, transfer.canonical.BASE, {}, recorded=receipt)
    return observed[0][0] if observed else None, result


def paired(inputs):
    for item, terms, receipt in inputs:
        obs, yes = traced(item, terms, receipt, lambda _: True)
        no = yes
        if obs is not None:
            other, no = traced(item, terms, receipt, lambda _: False)
            assert obs == other
        left, right = item[0][1]
        yield "agreement" if left & right else "impasse", obs, yes, no


def synthetic(split, widths, size, missing):
    seed = SEEDS[split]
    generated = episode.base.synth.worlds(widths, size, missing, seed)
    rows, terms = zip(*generated, strict=True)
    reduced = router.routing.refit.drop_returns(rows, seed+1)
    return {name: list(paired((item, fields, None) for item, fields in zip(
        episode.transport.delivery(reduced, seed+2, persistence), terms, strict=True)))
        for name, persistence in (("independent", 0), ("persistent", episode.transport.PERSISTENCE))}


def choose(obs, rules):
    return next((action for action, rule in reversed(rules)
                 if all(obs[i] == positive for i, positive in rule)), True)


def fit(train, validation):
    def prepare(panels):
        grouped = defaultdict(lambda: np.zeros(3, dtype=np.int64))
        groups = tuple(product(panels, ("agreement", "impasse")))
        for name, rows in panels.items():
            for label, obs, yes, no in rows:
                if obs is not None:
                    grouped[obs, (name, label)] += np.subtract(no[:3], yes[:3])
        views = tuple(sorted({obs for obs, _ in grouped}))
        effects = np.asarray([[grouped[obs, key] for key in groups] for obs in views])
        return views, effects

    def value(data, rules):
        views, effects = data
        skip = np.asarray([not choose(obs, rules) for obs in views], dtype=np.int64)
        delta = np.einsum("i,ijk->jk", skip, effects)
        score = int((delta @ np.asarray((200, -3, -1))).sum())
        return delta[:, 0].min() >= 0, score, delta.tolist()

    train, validation = map(prepare, (train, validation))
    atoms = tuple(product(range(len(FEATURES)), (False, True)))
    predicates = ((), *((atom,) for atom in atoms),
                  *((a, b) for a, b in combinations(atoms, 2) if a[0] != b[0]))
    rules, journal = (), []
    train_floor = dev_floor = 0
    for _ in range(3):
        best = None
        passing = Counter()
        for action, predicate in product((False, True), predicates):
            candidate = (*rules, (action, predicate))
            ok, score, train_delta = value(train, candidate)
            if not ok or score <= train_floor:
                continue
            passing["training"] += 1
            ok, dev, dev_delta = value(validation, candidate)
            if not ok or dev < dev_floor:
                continue
            passing["validation"] += 1
            rank = (score, dev, -len(predicate))
            if best is None or rank > best[0]:
                best = rank, candidate, train_delta, dev_delta
        journal.append({"passing": dict(passing)})
        if best is None:
            break
        (train_floor, dev_floor, _), rules, train_delta, dev_delta = best
        journal[-1].update(accepted=rules[-1], training_delta=train_delta, development_delta=dev_delta)
    return rules, journal


def score(rows, decide):
    counts, changes = Counter(), Counter()
    for label, obs, yes, no in rows:
        ask = obs is None or decide(obs)
        total = yes if ask else no
        counts[label, "presentations"] += 1
        counts[label, "eligible"] += obs is not None
        counts[label, "skipped"] += not ask
        for key, n in zip(METRICS, total, strict=True):
            counts[label, key] += n
        changes[label, str(yes[0]), str(total[0])] += 1
    return {"counts": router.sp.flatten(counts), "paired": router.sp.flatten(changes)}


def compare(panels, rules):
    return {label: {
        "query": score(rows, lambda _: True),
        "publish_only": score(rows, lambda _: False),
        "publish_if_covers_all_but_one": score(rows, lambda obs: not obs[2]),
        "learned": score(rows, lambda obs: choose(obs, rules)),
    } for label, rows in panels.items()}


def archived(rows):
    physical = [item[0] for _, item, *_ in rows]
    results = {"clean": list(paired((item, terms, receipt) for _, item, receipt, *_, terms in rows))}
    for name, p in (("independent", 0), ("persistent", episode.transport.PERSISTENCE)):
        results[name] = []
        for offset in range(12):
            tape = episode.transport.delivery(physical, frontier.SEED+offset, p)
            results[name].extend(paired((item, terms, receipt)
                for item, (_, _, receipt, *_, terms) in zip(tape, rows, strict=True)))
    return results


def evaluate():
    train = synthetic("training", (5, 6), 600, 2)
    val = synthetic("validation", (6,), 600, 3)
    rules, journal = fit(train, val)
    test = synthetic("holdout", (7, 8), 420, 3)
    sources = {"venezuela": transfer.cases(), "myanmar": episode.canonical.myanmar(0),
               "mali": episode.canonical.mali(transfer.load(
                   transfer.MALI/"evidence/joint-transfer/metrics.json"), 0)}
    return {"scope": "One irreversible query choice at the first opportunity under the fixed schedule.",
            "features": FEATURES, "seeds": SEEDS, "rules": rules, "fit": journal,
            "train": compare(train, rules), "development": compare(val, rules),
            "heldout": compare(test, rules),
            "transfers": {name: compare(archived(list(rows)), rules) for name, rows in sources.items()}}


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
