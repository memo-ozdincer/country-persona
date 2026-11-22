"""Enumerate the legal routing frontier under the stronger signed reply protocol."""
from collections import Counter
from functools import lru_cache
import json
from unittest.mock import patch

import learn_scope as scope_fit
import receipt_selection as selection
import workshop_transfer as transfer

episode = transfer.episode
router = transfer.router
BASELINES = (transfer.canonical.BASE, "set_first", "never")
SEED = 784429


def ordinary_when_possible(obs):
    return not obs[scope_fit.FEATURES.index("ordinary_target_available")]


def shortest(item, receipt):
    width, truth, local, opening, _ = item[0]
    full = (1 << width) - 1
    start = router.sp.opened(opening, local), 1, 0, 7

    @lru_cache(maxsize=None)
    def visit(state):
        ledger, actor, slot, _ = state
        if router.sp.terminal(ledger, full):
            assert all(not (ledger[2*r]&~menu or ledger[2*r+1]&menu)
                       for r, menu in enumerate(truth))
            return True, slot, 0, ()
        if slot >= width + 1:
            return False, slot, 0, ()
        observation, legal, ordinary = router.available(item, state)
        default = router.default(observation, transfer.canonical.BASE)
        actions = (default, *(a for a in legal if a != default))
        best = None
        for action in actions:
            next_state, checked, event = router.transition(
                item, state, action, legal, ordinary, receipt,
            )
            assert next_state[2] > slot
            solved, finish, checks, rest = visit(next_state)
            record = (solved, finish, checks+int(checked))
            key = episode.base.objective.utility(*record)
            if best is None or key > best[0]:
                step = {"slot": slot, "actor": actor, "action": action, "default": default,
                        "observation": observation, "ledger": next_state[0], "query": event}
                best = key, (*record, (step, *rest))
        return best[1]

    try:
        result = visit(start)
        return (*result, visit.cache_info().currsize)
    finally:
        visit.cache_clear()


def samples(rows):
    def setup():
        return selection.enabled(True, ordinary_when_possible)

    for key, item, receipt, *_, terms in rows:
        with patch.object(selection.reuse, "singleton_enabled", new=setup):
            with transfer.canonical.enabled(terms, "public", lambda: episode.delay.enabled(
                    lambda _: "immediate")):
                bound = shortest(item, receipt)
                fixed = {name: router.play(item, name, {}, recorded=receipt) for name in BASELINES}
        assert bound[0] or not any(outcome[0] for outcome in fixed.values())
        left, right = item[0][1]
        yield "/".join(key), ("agreement" if left & right else "impasse"), bound, fixed


def summarize(rows):
    counts, first_changes, route_needs, details = Counter(), Counter(), Counter(), {}
    for key, kind, (solved, slots, checks, witness, states), baselines in samples(rows):
        counts[kind, "presentations"] += 1
        counts[kind, "reachable"] += solved
        counts[kind, "any_fixed_reaches"] += any(value[0] for value in baselines.values())
        counts[kind, "visited_states"] += states
        for name, value in baselines.items():
            counts[kind, name] += value[0]
        if solved and not baselines[BASELINES[0]][0]:
            changes = [(step["slot"], step["action"]) for step in witness
                       if step["action"] != step["default"]]
            assert changes
            first_changes[kind, str(changes[0][1]), str(changes[0][0])] += 1
            route_needs[kind, len(changes)] += 1
            if not any(b[0] for b in baselines.values()) and kind not in details:
                details[kind] = {"row": key, "slots": slots, "checks": checks, "steps": witness}
    flatten = router.sp.flatten
    return {"counts": flatten(counts), "first_changes": flatten(first_changes),
            "changes_in_minimum_cost_witness": {f"{k}/{n}": v for (k, n), v in sorted(route_needs.items())},
            "example_outside_fixed_union": details}


def archive(rows):
    result = {"clean": summarize(rows)}
    original = [item[0] for _, item, *_ in rows]
    for kind, persistence in (("independent", 0), ("persistent", episode.transport.PERSISTENCE)):
        cohort = []
        for offset in range(12):
            tape = episode.transport.delivery(original, SEED+offset, persistence)
            cohort.extend(((*key, str(offset)), fresh, *rest)
                          for (key, _, *rest), fresh in zip(rows, tape, strict=True))
        result[kind] = summarize(cohort)
    return result


def evaluate():
    receipts = transfer.load(transfer.MALI/"evidence/joint-transfer/metrics.json")
    cases = {
        "venezuela": transfer.cases(),
        "myanmar": episode.canonical.myanmar(0),
        "mali": episode.canonical.mali(receipts, 0),
    }
    return {
        "scope": "Upper bound searches all router actions under fixed compound-reply preference and immediate retry. It knows the future simulated tape. Views in traces are decentralized; the optimizer is not.",
        "noise_seed": SEED,
        "routing_actions": {"request_set": selection.group.OFFER_SET,
                            "defer_check": selection.reuse.defer.DEFER,
                            "routine": selection.reuse.ROUTER.ROUTINE,
                            "match_scope": router.MATCH_SCOPE,
                            "hole_scope": router.HOLE_SCOPE},
        "receipts_sha256": transfer.digest(transfer.MALI/"evidence/joint-transfer/metrics.json"),
        "families": {name: archive(list(rows)) for name, rows in cases.items()},
    }


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
