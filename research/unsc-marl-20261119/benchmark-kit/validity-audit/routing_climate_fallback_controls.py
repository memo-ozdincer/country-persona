"""Check whether simple reply and pair-aware scripts reproduce the learned behavior."""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

import routing_climate_live_exchange as live
import routing_ftf_script_control as scripts

transfer = live.transfer
route = transfer.route
base = transfer.base
ANNOUNCED = live.channel.PLAN
RELEASE = base.space.OUT / "climate2021-language-gate/scores.json"
WRITTEN_VOTE = base.space.OUT / "ftf2020-visible-writer/scores.json"


def backup(reply_order):
    """If the named annex is unavailable, choose a nondefault held annex when possible."""
    table = np.zeros((8, 4), dtype=int)
    for mask in route.STATES:
        held = [int(action) for action in reply_order if mask & route.BITS[action]]
        if held:
            table[mask] = [held[0], *(q if q in held else held[min(1, len(held) - 1)] for q in route.ACTIONS[1:])]
    return table


def pair_aware(order):
    first, second, other = order
    ask, send = np.zeros(8, dtype=int), np.zeros(8, dtype=int)
    for mask in route.STATES:
        held = set(np.flatnonzero(route.SEND[mask, 1:]) + 1)
        if first in held and second not in held:
            ask[mask], send[mask] = second, first
        elif second in held:
            ask[mask], send[mask] = (0 if first in held else first), second
        elif other in held:
            send[mask] = other
    return ask, send, backup(order)


def disagreements(left, right):
    ask, send, reply = left
    q, a, b = right
    difference = (ask != q) | (send != a)
    return int(np.count_nonzero(difference[:, None] | (reply[:, ask].T != b[:, q].T)))


def choose(menu, priors, payoff, informed):
    table = route.receipt_matrix(payoff, route.TRAIN_LOSS)
    returns = np.asarray([[float((scripts.limit.pilot.cell_returns(policy, table) * (p.T if swap else p)).sum())
                           for policy, swap in menu.values()] for p in priors.values()])
    gains = returns - informed[:, None]
    n = len(menu)
    result = linprog(np.r_[np.zeros(n), -1.0], A_ub=np.c_[-gains, np.ones(len(priors))],
                     b_ub=np.zeros(len(priors)), A_eq=np.r_[np.ones(n), 0.0][None, :], b_eq=[1.0],
                     bounds=[(0, 1)] * n + [(None, None)], method="highs")
    assert result.success, result.message
    weights = result.x[:-1]
    assert np.isclose(weights.sum(), 1.) and np.isclose(min(gains @ weights), result.x[-1])
    adversary = -result.ineqlin.marginals
    assert np.isclose(adversary.sum(), 1.) and np.all(adversary >= 0)
    assert np.isclose(max(adversary @ gains), result.x[-1])
    return {name: (policy, swap, mass) for (name, (policy, swap)), mass in zip(menu.items(), weights, strict=True)
            if mass > 1e-10}, float(result.x[-1])


def pack():
    frozen = live.read(ANNOUNCED)["plans"]
    learned = [(base.space.as_policy(p), swap, mass) for p, swap, mass in frozen["learned"]]
    old_replay = [(base.space.as_policy(p), swap, mass) for p, swap, mass in frozen["scripted"]]
    strongest, _, weight = max(learned, key=lambda row: row[2])
    generic_reply = backup([1, 2, 3])
    shortcut = (strongest[0], strongest[1], generic_reply)
    full_shortcut = pair_aware((1, 2, 3))
    assert disagreements(strongest, shortcut) == disagreements(strongest, full_shortcut) == 0

    simple, _, _ = scripts.select()
    expanded = dict(simple)
    for order_zero in base.ORDERS:
        order = tuple(value + 1 for value in order_zero)
        standard = base.remap_policy(route.scripted(), order_zero)
        modified = (*standard[:2], backup(order))
        for swapped in (False, True):
            expanded[f"backup:{order}:{swapped}"] = (modified, swapped)
            expanded[f"pair:{order}:{swapped}"] = (pair_aware(order), swapped)

    priors, _, _ = transfer.original.selections()
    announced = transfer.payoff(transfer.task())
    assert np.array_equal(announced, transfer.original.public_payoff())
    payoffs = {"announced": announced, "climate_release": np.asarray(live.read(RELEASE)["score"]["release"]),
               "written_vote_release": np.asarray(live.read(WRITTEN_VOTE)["eligible_vector"])}
    table = route.receipt_matrix(announced, route.TRAIN_LOSS)
    informed = np.asarray([route.evaluate(route.best_silent(p, table), p, announced, route.TRAIN_LOSS)["net"]
                           for p in priors.values()])
    old_exact, old_bound = choose(simple, priors, announced, informed)
    new_exact, new_bound = choose(expanded, priors, announced, informed)
    assert new_bound >= old_bound - 1e-9
    mixtures = {"learned": learned, "published_script": old_replay, "original_menu_exact": old_exact.values(),
                "expanded_menu_exact": new_exact.values()}
    out = {}
    for metric, payoff in payoffs.items():
        out[metric] = {}
        for name, prior in priors.items():
            values = {tag: sum(mass * route.evaluate(p, prior.T if swap else prior, payoff, route.TRAIN_LOSS)["net"]
                               for p, swap, mass in group) for tag, group in mixtures.items()}
            out[metric][name] = {**values, "learned_minus_expanded": values["learned"] - values["expanded_menu_exact"]}
    return {
        "scope": "Retrospective scripted controls sized and selected only on the announced payoff. Same priors, loss and fees. "
                 "The release metrics reuse the audited climate and 2020 written-vote language banks. "
                 "The weights are unchanged between cases. Script design is exposed development.",
        "plan_sha256": live.digest(ANNOUNCED), "climate_release_sha256": live.digest(RELEASE),
        "written_vote_release_sha256": live.digest(WRITTEN_VOTE),
        "highest_mass_learned_component": weight, "reachable_worlds": 64,
        "worlds_where_its_actions_differ_from_paired_script": disagreements(strongest, full_shortcut),
        "worlds_where_its_actions_differ_with_generic_backup": disagreements(strongest, shortcut),
        "selection": {"original_menu_size": len(simple), "expanded_menu_size": len(expanded),
                      "original_worst_gain_vs_prior_informed_silent": old_bound,
                      "expanded_worst_gain_vs_prior_informed_silent": new_bound,
                      "original_weights": {key: mass for key, (_, _, mass) in old_exact.items()},
                      "expanded_weights": {key: mass for key, (_, _, mass) in new_exact.items()}},
        "scores": out,
    }


if __name__ == "__main__":
    print(json.dumps(pack(), indent=2))
