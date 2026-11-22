"""One joint fit with a paid negative receipt, evaluated on frozen DRC records."""
from collections import defaultdict
from functools import lru_cache
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import results
from policy_replay import policy
from specialist_fit import optimizer

HERE = results.HERE
relay = policy.relay
shift = policy.shift
EMPTY = "no_requested_card"


def branches(world, pending, contact, probabilities, feedback):
    held = tuple(i for i in pending if i in world[contact])
    reply = bool(held) or feedback
    fee = relay.QUESTION_COST + relay.LINK * relay.REPLY_COST * reply
    if not held:
        if feedback:
            return fee, ((EMPTY, relay.RECEIPT, ()), (None, 1 - relay.RECEIPT, ()))
        return fee, ((None, 1., ()),)
    events = []
    for (card, (choice, action)) in zip(held, probabilities(held), strict=True):
        events.extend(((card, relay.RECEIPT * choice, action),
                       (None, (1 - relay.RECEIPT) * choice, action)))
    return fee, events


def remaining(pending, observed):
    return tuple(card for card in pending if card != observed)


def train_paths():
    scores = optimizer.scores()
    states = {}
    compiled = defaultdict(float)
    width = 0

    def action(key, choice, size):
        nonlocal width
        if key not in states:
            states[key] = width, size
            width += size
        return states[key][0] + choice

    @lru_cache(None)
    def walk(target, anchor, world, pending, history):
        value = scores[target, anchor, pending]
        if not pending or len(history) == optimizer.HORIZON:
            return [((), 1., 0., not pending, value, 0)]
        key = ("requester", target, anchor, history)
        rows = [((action(key, 0, 3),), 1., 0., False, value, 0)]
        for contact in range(2):
            selected = action(key, contact + 1, 3)

            def reply(held):
                if len(held) == 1:
                    return ((1., ()),)
                return tuple((1., (action(("responder", pending, world[contact]), i, 2),))
                             for i in range(2))

            fee, outcomes = branches(world, pending, contact, reply, True)
            for seen, mass, reply_action in outcomes:
                for tail, p, cost, done, score, count in walk(
                        target, anchor, world, remaining(pending, seen), history + ((contact, seen),)):
                    rows.append(((selected,) + reply_action + tail, mass * p, fee + cost, done, score, count + 1))
        return rows

    for target, anchor in relay.SCENARIOS:
        pending = tuple(i for i in target if i != anchor)
        prior = shift.distribution(pending, shift.TRAIN_STRENGTH, 0)
        for world, probability in prior.items():
            for actions, mass, cost, done, score, count in walk(target, anchor, world, pending, ()):
                compiled[actions, round(cost, 8), done, score, count] += mass * probability / len(relay.SCENARIOS)
    path_width = max(len(row[0]) for row in compiled)
    traces = np.array([actions + (-1,) * (path_width - len(actions)) for actions, *_ in compiled])
    outcomes = np.array([row[1:] for row in compiled], dtype=float)
    return states, traces, outcomes, {"design_mixture": np.array(list(compiled.values()))}


def replay(weights, target, anchor, prior, canonical=False, blind=False):
    """When blind, erase only the negative receipt from the policy's observation."""
    @lru_cache(None)
    def walk(world, pending, history):
        if not pending or len(history) == optimizer.HORIZON:
            return {pending: (1., 0., 0.)}
        probabilities = weights["requester", target, anchor, history]
        out = defaultdict(lambda: [0., 0., 0.])
        out[pending][0] = probabilities[0]
        for contact, contact_p in enumerate(probabilities[1:]):
            def reply(held):
                if len(held) == 1:
                    choice = (1.,)
                elif canonical:
                    choice = (1., 0.)
                else:
                    choice = weights["responder", pending, world[contact]]
                return tuple((weight, ()) for weight in choice)

            fee, observations = branches(world, pending, contact, reply, True)
            for seen, likelihood, _ in observations:
                visible = None if blind and seen == EMPTY else seen
                for final, (mass, cost, count) in walk(world, remaining(pending, seen),
                                                      history + ((contact, visible),)).items():
                    scale = contact_p * likelihood
                    row = out[final]
                    row[0] += scale * mass
                    row[1] += scale * (cost + fee * mass)
                    row[2] += scale * (count + mass)
        return out

    pending = tuple(i for i in target if i != anchor)
    marginal = defaultdict(lambda: [0., 0., 0.])
    for world, exogenous in prior.items():
        for final, terminal_metrics in walk(world, pending, ()).items():
            for i, metric in enumerate(terminal_metrics):
                marginal[frozenset(final)][i] += exogenous * metric
    return marginal


def script_transitions(belief, pending, contact, blind=False):
    posterior = defaultdict(lambda: defaultdict(float))
    total_fee = 0.
    for world, mass in belief.items():
        fee, outcomes = branches(world, tuple(sorted(pending)), contact,
                                 lambda held: ((1., ()),) + ((0., ()),) * (len(held) - 1), True)
        total_fee += fee * mass
        for seen, chance, _ in outcomes:
            if chance:
                visible = None if blind and seen == EMPTY else seen
                posterior[visible][world] += chance * mass
    return total_fee, posterior


def run():
    states, actions, outcomes, mass = train_paths()
    history, weights = optimizer.fit(states, actions, outcomes, mass)
    learned = {key: weights["joint_learned"][offset:offset + size].tolist()
               for key, (offset, size) in states.items()}
    # Check the traversal against the exact objective through an independent
    # forward distribution over terminal sets, costs and contact attempts.
    scores = optimizer.scores()
    totals = []
    for target, anchor in relay.SCENARIOS:
        prior = shift.distribution(set(target) - {anchor}, shift.TRAIN_STRENGTH, 0)
        dist = replay(learned, target, anchor, prior)
        assert abs(sum(p for p, _, _ in dist.values()) - 1.) < 1e-9
        totals.append(sum(p * (scores[target, anchor, tuple(sorted(left))] - 35) - fees
                          for left, (p, fees, _) in dist.items()))
    assert abs(sum(totals) / len(totals) - history[-1]["record_reward"]) < 1e-9

    original = results.load(results.EVIDENCE / "policy-replay.json")
    observed = results.load(results.EVIDENCE / "results.json")["field_packets"]
    case = results.load(results.writer.CASE)
    bank = results.verified_bank(case)
    ids = tuple(case["sources"])
    mapping = {(r["anchor"], *r["other_cards"]): r for r in original["table_alignment"]["rows"]}
    conditions = {}
    for label, baseline in original["conditions"].items():
        strength, desk, kind = shift.CONDITIONS[label]
        hint = 1 - desk if kind == "wrong_hint" else desk
        rows = []
        for (target, anchor), prior_row in zip(relay.SCENARIOS, baseline["rows"], strict=True):
            pending = [i for i in target if i != anchor]
            idx = (ids[anchor], *(ids[i] for i in pending))
            prior = shift.distribution(pending, strength, desk, kind)
            distributions = {}
            for name, blind, canonical in (("learned_ack", False, False),
                                           ("learned_ack_erased", True, False),
                                           ("learned_ack_canonical_desk", False, True)):
                def localized(weights, target, anchor, prior, slot_is_canonical):
                    return replay(weights, target, anchor, prior, slot_is_canonical, blind)
                with patch.object(shift.transfer, "outcomes", localized):
                    distributions[name] = shift.remap(learned, prior, target, anchor, mapping[idx],
                                                      (hint, 1 - hint), canonical)
            with patch.object(relay, "transitions", script_transitions):
                distributions["fixed_ack"] = policy.script(target, anchor, ids, bank, prior, False)
                distributions["adaptive_ack"] = policy.script(target, anchor, ids, bank, prior, True)
            with patch.object(relay, "transitions", lambda *args: script_transitions(*args, blind=True)):
                distributions["adaptive_ack_erased_replanned"] = policy.script(target, anchor, ids, bank, prior, True)
            assert prior_row["anchor"] == idx[0] and prior_row["target"] == [ids[i] for i in target]
            metrics = {name: policy.benefits(target, anchor, ids, dist, observed, bank)
                       for name, dist in distributions.items()}
            rows.append({"target": prior_row["target"], "anchor": idx[0], "metrics": {
                **metrics, **{k + "_no_ack": prior_row["scores"][k]
                              for k in ("specialist", "best_fixed", "best_adaptive")}}})
        conditions[label] = {"mean": shift.transfer.mean([r["metrics"] for r in rows]), "rows": rows}

    return {"scope": "One written-vote-only joint fit with a paid empty receipt. DRC supplies the frozen "
                     "authored alignment and generated endpoint at transfer. Scripts plan with the true roster "
                     "prior and the authored terminal score. Ablations keep the attempt charge.",
            "training": history, "trajectory_rows": len(actions), "unique_local_states": len(states),
            "conditions": conditions, "policy": [{"local_state": state, "probabilities": prob}
                                                  for state, prob in learned.items()],
            "pins": {str(p.relative_to(HERE.parent)): results.writer.runner.digest(p) for p in (
                Path(__file__), HERE / "evidence/policy-replay.json", HERE / "evidence/results.json",
                Path(optimizer.__file__))}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
