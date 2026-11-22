"""Train a shared local actor from counterfactual routing returns."""
from collections import Counter, defaultdict
from contextlib import contextmanager
from functools import lru_cache
from itertools import combinations
import json
from pathlib import Path
import sys
from unittest.mock import patch

import numpy as np

HERE = Path(__file__).resolve().parent
VENEZUELA = HERE / "crossbench/venezuela"
sys.path.insert(0, str(VENEZUELA))

import model_receipt
import noisy_frontier as frontier

router, transfer, episode, selection = frontier.router, frontier.transfer, frontier.episode, frontier.selection
BASE = transfer.canonical.BASE
ACTIONS = (-4, -3, 0, 1, 2, 3, 4)
SEEDS = {"train": 369029, "dev": 158299, "heldout": 449311, "archive": 767821}
MODES = ("clean", "independent", "persistent")
MARGINS = (0., 0.025, 0.05, 0.10, 0.18, 0.30, 0.48)
LABELS = ("agreement", "impasse")
FEATURES = (
    "intercept", "horizon", "live", "own_eligible_live", "own_excluded_live",
    "own_unknown_live", "peer_offer_live", "peer_offer_known_eligible",
    "peer_offer_known_excluded", "peer_offer_unknown", "own_offer_live",
    "own_offer_matches_peer", "remaining_missing_my_yes", "peer_check_credit",
    "my_check_credit", "peer_receipt_cached", "my_receipt_cached",
    "query_credit", "first_turn", "few_live", "single_known_live_acceptance",
    "local_state_covers_live", "routine_is_check", "routine_is_bundle",
    *(f"legal_{action}" for action in ACTIONS), *(f"default_{action}" for action in ACTIONS),
)
FRONTIER_FEATURES = len(FEATURES) - 2 * len(ACTIONS)
INTERACTIONS = tuple(combinations(range(1, FRONTIER_FEATURES), 2))


@contextmanager
def protocol(terms):
    with patch.object(selection.reuse, "singleton_enabled",
                      new=lambda: selection.enabled(True, frontier.ordinary_when_possible)):
        with transfer.canonical.enabled(terms, "public",
                                        lambda: episode.delay.enabled(lambda _: "immediate")):
            yield


def vector(item, state, legal, normal, default):
    public, actor, turn, credit = state
    peer = 1-actor
    width = item[0][0]
    yes, no = item[0][2][actor]
    live = ((1<<width)-1) & ~(public[1]|public[3])
    theirs = public[2*peer] & live
    mine = public[2*actor] & live
    unknown = live & ~(yes|no)
    main = (
        1., (width+1-turn)/(width+1), live.bit_count()/width,
        (yes&live).bit_count()/width, (no&live).bit_count()/width,
        unknown.bit_count()/width, bool(theirs), bool(theirs&yes), bool(theirs&no),
        bool(theirs&unknown), bool(mine), bool(mine&theirs), bool(mine&~yes),
        bool(credit&(1<<peer)), bool(credit&(1<<actor)), bool(credit&(selection.reuse.CACHE<<peer)),
        bool(credit&(selection.reuse.CACHE<<actor)), bool(credit&selection.reuse.ROUTER.CREDIT),
        turn==0, live.bit_count()<=3, (yes&live).bit_count()==1, not unknown,
        normal[2][0]==episode.delay.CHECK, normal[2][0]==router.routing.BUNDLE,
        *(action in legal for action in ACTIONS), *(action==default for action in ACTIONS),
    )
    assert len(main)==len(FEATURES)
    return np.asarray((*main, *(main[a]*main[b] for a,b in INTERACTIONS)), dtype=np.float64)


def world_label(item):
    left, right = item[0][1]
    return "agreement" if left&right else "impasse"


def terminal_record(item, state):
    width = item[0][0]
    solved = router.sp.terminal(state[0], (1<<width)-1)
    if solved or state[2] >= width+1:
        return 200*int(solved)-3*state[2]
    return None


def counterfactual(item, terms):
    width, _, local, opening, _ = item[0]
    start = router.sp.opened(opening, local), 1, 0, 7
    samples = []

    @lru_cache(maxsize=None)
    def visit(state):
        terminal = terminal_record(item, state)
        if terminal is not None:
            return terminal, terminal
        obs, legal, routine = router.available(item, state)
        default = router.default(obs, BASE)
        values = {}
        for action in legal:
            following, paid, _ = router.transition(item, state, action, legal, routine)
            fixed, optimal = visit(following)
            values[action] = fixed-int(paid), optimal-int(paid)
        if len(legal) > 1:
            local_view = vector(item, state, legal, routine, default)
            samples.extend((action, local_view, *((v-b)/200 for v, b in zip(
                              outcome, values[default], strict=True)))
                           for action, outcome in values.items() if action != default)
        return values[default][0], max(v[1] for v in values.values())

    try:
        with protocol(terms):
            visit(start)
        return samples
    finally:
        visit.cache_clear()


def train(panels):
    data = defaultdict(list)
    for rows in panels.values():
        for item, terms, _ in rows:
            for action, view, one, best in counterfactual(item, terms):
                data[action].append((view, one, best))
    models = {"fixed_continuation": {}, "optimized_continuation": {}}
    counts = {}
    for action, rows in data.items():
        x = np.stack([row[0] for row in rows])
        y = np.asarray([row[1:] for row in rows])
        weights = np.linalg.solve(x.T@x + 18*np.eye(x.shape[1]), x.T@y)
        counts[action] = {"samples": len(rows), "positive_deltas": (y > 0).sum(axis=0).tolist(),
                          "negative_deltas": (y < 0).sum(axis=0).tolist()}
        for index, model in enumerate(models):
            models[model][action] = weights[:, index]
    return models, counts


def simulate(item, terms, receipt, policy, mode=BASE):
    # The actor sees only the packed feature vector and legal move indices.
    # Routing, signing, and delivery are handled by the same frozen runtime.
    chosen = []
    with protocol(terms):
        available, default = router.available, router.default

        def observe(row, state):
            obs, legal, routine = available(row, state)
            anchor = default(obs, mode)
            if len(legal)>1:
                picked = policy(vector(row, state, legal, routine, anchor), legal, anchor)
                if picked != anchor:
                    chosen.append((state[2], anchor, picked))
            else:
                picked = anchor
            return (obs, picked), legal, routine

        with patch.object(router, "available", new=observe), patch.object(
                router, "default", new=lambda obs, _: obs[1]):
            result = router.play(item, mode, {}, recorded=receipt)
    return result, chosen


def no_override(_, legal, default):
    return default


def actor(weights, margin):
    if margin is None:
        return no_override

    def choose(x, legal, default):
        rated = [(float(x @ weights[a]), a) for a in legal if a != default and a in weights]
        return max(rated)[1] if rated and max(rated)[0] > margin else default

    return choose


def collect(rows, policy=no_override, mode=BASE):
    counts, choices, paths = Counter(), Counter(), []
    for item, terms, receipt in rows:
        label = world_label(item)
        metrics, changes = simulate(item, terms, receipt, policy, mode)
        for name, count in zip(("certificate", "slots", "checks", "queries", "answers", "scope"),
                               metrics, strict=True):
            counts[label, name] += count
        counts[label, "presentations"] += 1
        counts[label, "episodes_changed"] += bool(changes)
        counts[label, "actor_overrides"] += len(changes)
        for slot, anchor, action in changes:
            choices[label, str(anchor), str(action)] += 1
        paths.append(tuple(metrics))
    return counts, {"counts": router.sp.flatten(counts), "actions": router.sp.flatten(choices)}, paths


def utility(counts):
    return sum(episode.base.objective.utility(*(counts[class_, k] for k in (
        "certificate", "slots", "checks"))) for class_ in LABELS)


def select(panels, model):
    baselines = {name: collect(rows)[0] for name, rows in panels.items()}
    best = None
    trials = {}
    floor = sum(map(utility, baselines.values()))
    for margin in MARGINS:
        outcome = {name: collect(rows, actor(model, margin)) for name, rows in panels.items()}
        gain = sum(utility(results[0]) for results in outcome.values())-floor
        protected = all(results[0][label, "certificate"] >= baselines[name][label, "certificate"]
                        for name,results in outcome.items() for label in LABELS)
        trials[margin] = {"gain": gain, "guard": protected,
                          "panels": {k: v[1] for k,v in outcome.items()}}
        if protected and gain>0 and (best is None or gain>best[0]):
            best = gain, margin
    active = max(trials, key=lambda m: trials[m]["gain"])
    return {"selected": None if best is None else best[1], "max_utility_without_guard": active,
            "trials": trials}


def reports(panels, fitted, picks):
    arms = {
        **{name: (no_override, name) for name in frontier.BASELINES},
        **{f"{name}/{kind}": (actor(model, thresholds[value]), BASE)
           for name, model in fitted.items() for thresholds in (picks[name],)
           for kind, value in (("selected", "selected"), ("unguarded", "max_utility_without_guard"))},
    }
    all_results = {}
    for cohort, rows in panels.items():
        scores = {name: collect(rows, policy, mode) for name,(policy, mode) in arms.items()}
        reference = scores[BASE][2]
        all_results[cohort] = {}
        for name, (_, report, paths) in scores.items():
            pairs = Counter((world_label(item), str(a[0]), str(b[0]))
                            for (item, _, _), a, b in zip(rows, reference, paths, strict=True))
            all_results[cohort][name] = {**report, "paired": router.sp.flatten(pairs)}
    return all_results


def synth(split, widths, size, missing):
    seed = SEEDS[split]
    rows, docs = zip(*episode.base.synth.worlds(widths, size, missing, seed), strict=True)
    reduced = router.routing.refit.drop_returns(rows, seed+1)
    good = router.guard.messages(rows, seed+2, 0., 0.)
    independent = episode.transport.delivery(reduced, seed+2, 0.)
    persistent = episode.transport.delivery(reduced, seed+2, episode.transport.PERSISTENCE)
    return {name: [(row, terms, None) for row, terms in zip(data, docs, strict=True)]
            for name, data in zip(MODES, (good, independent, persistent), strict=True)}


def archived(rows):
    result = {"clean": [(item, terms, later) for _, item, later, *_, terms in rows]}
    original = [item[0] for _,item,*_ in rows]
    for mode, persistence in (("independent", 0.), ("persistent", episode.transport.PERSISTENCE)):
        result[mode] = []
        for seed in range(SEEDS["archive"], SEEDS["archive"]+10):
            tape = episode.transport.delivery(original, seed, persistence)
            result[mode].extend((item, terms, later)
                                for item, (_, _, later, *_, terms) in zip(tape, rows, strict=True))
    return result


def evaluate():
    data = synth("train", (5, 6), 150, 2)
    dev = synth("dev", (6,), 150, 3)
    tested = synth("heldout", (7, 8), 150, 3)
    fits, samples = train(data)
    picks = {kind: select(dev, model) for kind, model in fits.items()}
    path = VENEZUELA/"evidence/model-receipt/metrics.json"
    measured = transfer.load(path)["conditions"]["pooled"]
    projected = list(model_receipt.input_rows(
        measured["signs_before_admission"], measured["scope_before_admission"], "modeled"))
    archives = {"venezuela_model_receipts": projected, "myanmar": list(episode.canonical.myanmar(0)),
                "mali": list(episode.canonical.mali(transfer.load(
                    transfer.MALI/"evidence/joint-transfer/metrics.json"), 0))}
    return {
        "scope": "Offline shared decentralized action selection trained on synthetic team rewards. The optimized continuation critic can see future training fault tapes. Both actors deploy one learned function on their permitted observations.",
        "features": FEATURES, "interactions": INTERACTIONS, "seeds": SEEDS, "margins": MARGINS,
        "samples_by_action": samples, "validation": picks,
        "models": {kind: {action: row.tolist() for action,row in model.items()} for kind, model in fits.items()},
        "heldout": reports(tested, fits, picks),
        "workshops": {family: reports(archived(rows), fits, picks) for family, rows in archives.items()},
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
