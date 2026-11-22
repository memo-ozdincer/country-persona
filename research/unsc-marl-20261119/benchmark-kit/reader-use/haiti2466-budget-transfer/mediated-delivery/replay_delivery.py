"""Replay realized partial evidence through frozen policies and an exact comparator."""
import argparse
from copy import deepcopy
from itertools import product
import json
from pathlib import Path
import sys

import numpy as np

from run_delivery import HERE, base
sys.path.insert(0, str(HERE.parent))
import plan

fit, joint, D, R = plan.fit, plan.joint, plan.D, plan.R
IDEAL = np.tile(np.asarray([0, 3, 12, 48]), (4, 1))
PRESENT = np.array([sum(1 << i for i in range(3) if mask & (3 << (2 * i))) for mask in range(64)])
MASKS = np.arange(64)


def budget_values(packet):
    data = []
    for mask in MASKS:
        filtered = deepcopy(packet)
        for desk, card in enumerate(filtered["cards"]):
            card["atoms"] = [atom for i, atom in enumerate(card["atoms"]) if mask & (1 << (2 * desk + i))]
        data.append(base.variants(filtered, 7, 70)["selected"])
    return np.asarray([x["points"] + packet["base_points"] for x in data]), data


def first_mass(left, right, prior, openings):
    first = np.zeros((8, 4, 64))
    for l, r, deliver_l, deliver_r in product(range(8), range(8), (False, True), (False, True)):
        a, b = left[l], right[r]
        mask = (openings[a] if deliver_l else 0) | (openings[b] if deliver_r else 0)
        weight = prior[l, r] * (1 - D.LOSS if deliver_l else D.LOSS) * (1 - D.LOSS if deliver_r else D.LOSS)
        first[r, b, mask] += weight
    assert abs(first.sum() - 1) < 1e-12
    return first


def exact(first, value, admission, quiet=False):
    maps = fit.MAPS[:1] if quiet else fit.MAPS
    nominal = D.one_hot(maps[:, PRESENT])
    heard = (1 - D.LOSS) * nominal + D.LOSS * fit.ERASURE
    terminal = (1 - D.LOSS) * value[MASKS[:, None, None] | admission[None, :, :]]
    terminal += D.LOSS * value[:, None, None]
    terminal -= D.SEND_COST
    replies = np.einsum("rbm,pmt,mtc->prbtc", first, heard, terminal, optimize=True)
    replies = np.where(D.FINAL_LEGAL[None, ...], replies, -np.inf)
    net = replies.max(-1).sum((1, 2, 3)) - D.QUERY_COST[maps[:, PRESENT]] @ first.sum((0, 1))
    pick = int(net.argmax())
    return maps[pick], replies[pick].argmax(-1)


def measure(team, prior, value, opening, replies):
    left, right, ask, reply = team
    first = first_mass(left, right, prior, opening)
    questions = ask[PRESENT]
    heard = (1 - D.LOSS) * D.one_hot(questions) + D.LOSS * fit.ERASURE
    sent = np.einsum("rbm,mt,rbtc->mtc", first, heard, D.one_hot(reply), optimize=True)
    final = D.LOSS * sent.sum((1, 2))
    destination = (MASKS[:, None, None] | replies[None, :, :]).ravel()
    np.add.at(final, destination, (1 - D.LOSS) * sent.ravel())
    assert abs(final.sum() - 1) < 1e-12
    costs = (prior.sum(1) @ D.SEND_COST[left] + prior.sum(0) @ D.SEND_COST[right]
             + first.sum((0, 1)) @ D.QUERY_COST[questions] + sent.sum((0, 1)) @ D.SEND_COST)
    opening_count = prior.sum(1) @ (left != 0) + prior.sum(0) @ (right != 0)
    reply_count = float(sent[:, :, 1:].sum())
    return {"points": float(final @ value), "net": float(final @ value - costs),
            "cost_points": float(costs),
            "queries": float(first.sum((0, 1)) @ (questions != 0)),
            "reply_sends": reply_count,
            "expected_note_calls": float(opening_count + reply_count),
            "expected_fields": float(final @ np.array([int(m).bit_count() for m in MASKS])),
            "reply_table": np.asarray(reply).tolist(), "request_by_coarse_receipt": np.asarray(ask).tolist()}


def direct_net(team, prior, value, opening, replies):
    left, right, ask, reply = team
    total = 0.
    for l, r in product(range(8), repeat=2):
        a, b = left[l], right[r]
        for left_sent, right_sent, asked, reply_sent in product((False, True), repeat=4):
            arrivals = (left_sent, right_sent, asked, reply_sent)
            probability = prior[l, r] * float(np.prod([1 - D.LOSS if arrived else D.LOSS for arrived in arrivals]))
            initial = (opening[a] if left_sent else 0) | (opening[b] if right_sent else 0)
            question = ask[PRESENT[initial]]
            heard = question if asked else 0
            source = reply[r, b, heard]
            final = initial | (replies[heard, source] if reply_sent else 0)
            cost = D.SEND_COST[a] + D.SEND_COST[b] + D.QUERY_COST[question] + D.SEND_COST[source]
            total += probability * (value[final] - cost)
    return total


def run(admission_report):
    packet = base.read(base.PACKET)
    forecast = base.read(base.FORECAST)
    actual = np.asarray(admission_report["admitted_masks"])
    assert actual.shape == (4, 4) and np.all(actual == (actual & IDEAL))
    value, chosen = budget_values(packet)
    pub = np.asarray(forecast["curves"]["70"]["prefix"])
    whole = np.asarray(forecast["curves"]["70"]["whole"])
    combined = np.asarray([sum(3 << (2 * i) for i in range(3) if m & (1 << i)) for m in range(8)])
    assert np.array_equal(value[combined], pub) and np.max(value) < 70
    model = base.read(plan.FIT)["training"]["budget_fit"]
    evaluations = {}
    for label in fit.live.PRIORS:
        prior = R.TEST_PRIORS[label]
        team, _ = plan.budget.adaptive.contextual_policies(pub, prior, model)
        left, right, _, responder = team
        mass = joint.opening(left, right, prior)
        frozen = {"learned": team,
                  "learned_responder_silence": (left, right, np.zeros(8, dtype=int), responder),
                  "exact_ideal_no_request": (left, right, *fit.exact(pub, mass, fit.PERFECT, independent=True)),
                  "declared_excerpt_planner": (left, right, *fit.exact(pub, mass, fit.PERFECT)),
                  "declared_whole_planner": (left, right, *fit.exact(whole, mass, fit.PERFECT))}
        conditions = {"perfect": (IDEAL[0], IDEAL), "observed": (actual[0], actual),
                      "opening_errors_only": (actual[0], IDEAL), "followup_errors_only": (IDEAL[0], actual)}
        results = {stage: {name: measure(roles, prior, value, initial, tail) for name, roles in frozen.items()}
                   for stage, (initial, tail) in conditions.items()}
        for name, roles in frozen.items():
            expected = joint.metric(roles, prior, pub, fit.PERFECT)
            assert abs(expected["net"] - results["perfect"][name]["net"]) < 1e-10
        measured_first = first_mass(left, right, prior, actual[0])
        for name, quiet in (("hindsight_no_request", True), ("hindsight_joint", False)):
            roles = (*team[:2], *exact(measured_first, value, actual, quiet))
            results["observed"][name] = measure(roles, prior, value, actual[0], actual)
        for stage, (openings, replies) in conditions.items():
            replay = direct_net(team, prior, value, openings, replies)
            assert abs(replay - results[stage]["learned"]["net"]) < 1e-10
        maximum = results["observed"]["hindsight_joint"]["net"]
        assert all(r["net"] <= maximum + 1e-10 for r in results["observed"].values())
        evaluations[label] = results
    paths = {}
    uniform_team, _ = plan.budget.adaptive.contextual_policies(pub, R.TEST_PRIORS["uniform"], model)
    _, right, ask, reply = uniform_team
    for world, row in forecast["worlds"].items():
        first = 0
        for c in row["openings"]:
            first |= actual[0, c]
        assert PRESENT[first] == row["receipt"] or not np.array_equal(actual[0], IDEAL[0])
        changed = {}
        _, r = row["inventories"]
        q = ask[PRESENT[first]]
        fixed_query = {"learned": (q, reply[r, right[r], q]), "silence": (0, reply[r, right[r], 0]),
                       "fixed_missing": tuple(row["tail"]["fixed_missing"])}
        for role, (asking, c) in fixed_query.items():
            recv = first | actual[asking, c]
            selected = chosen[recv]
            body = "\n".join(g["desk"] + ": " + " ".join(g["statements"]) for g in selected["evidence"])
            assert len(body.split()) == selected["words"] <= 70
            changed[role] = {"query": int(asking), "reply": int(c), "admitted_fields": int(recv),
                             "supplementary_points": selected["points"], "words": selected["words"],
                             "claims": selected["ids"], "record": packet["public"] + "\n\n" + body}
        paths[world] = changed
    return {"cases": evaluations, "selected_no_erasure_paths": paths}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("admission", type=Path)
    print(json.dumps(run(base.read(parser.parse_args().admission)), ensure_ascii=False, indent=2))
