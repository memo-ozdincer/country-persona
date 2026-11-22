"""Fit requester and responder policies with exact finite-horizon policy gradients."""
from collections import defaultdict
from functools import lru_cache
import json

import numpy as np

import adaptive_relay as relay

HORIZON = 3
STEPS = 180
LR = .08
REQUEST_ACTIONS = 3  # stop, A, B


def scores():
    task = relay.archive.load()
    return {(target, anchor, pending): relay.assembly(
        task, target, [relay.archive.packet(i) for i in target if i not in pending])["final_record_score"]
        for target, anchor in relay.SCENARIOS
        for pending in ((), *((i,) for i in target if i != anchor),
                        tuple(i for i in target if i != anchor))}


def build(delivery=relay.LINK):
    """Enumerate trajectories including stochastic links and both local policies."""
    records = scores()
    states = {}
    paths = defaultdict(lambda: np.zeros(len(relay.WORLDS)))

    def action(state, choice, width):
        if state not in states:
            start = sum(n for _, n in states.values())
            states[state] = start, width
        return states[state][0] + choice

    @lru_cache(None)
    def spell(target, anchor, world, pending, history):
        if not pending or len(history) == HORIZON:
            return [((), 1., 0., not pending, records[target, anchor, pending], 0)]
        request_state = ("requester", target, anchor, history)
        stopped = action(request_state, 0, REQUEST_ACTIONS)
        rows = [((stopped,), 1., 0., False, records[target, anchor, pending], 0)]
        for contact in (0, 1):
            sent = action(request_state, contact + 1, REQUEST_ACTIONS)
            held = tuple(i for i in pending if i in world[contact])
            # Request loss cannot contribute a reply gradient. Split the two
            # loss paths so incurred cost is replayable as actually charged.
            outcome = [(None, 1 - delivery, relay.QUESTION_COST, ())]
            if not held:
                outcome.append((None, delivery, relay.QUESTION_COST, ()))
            else:
                for index, card in enumerate(held):
                    reply = () if len(held) == 1 else (action(("responder", pending, world[contact]), index, 2),)
                    fee = relay.QUESTION_COST + relay.REPLY_COST
                    outcome.extend(((None, delivery * (1 - delivery), fee, reply),
                                    (card, delivery ** 2, fee, reply)))
            for observed, mass, fee, reply in outcome:
                then = tuple(i for i in pending if i != observed)
                for tail, prob, cost, complete, quality, contacts in spell(
                        target, anchor, world, then, history + ((contact, observed),)):
                    rows.append(((sent,) + reply + tail, mass * prob, fee + cost, complete, quality, contacts + 1))
        return rows

    for target, anchor in relay.SCENARIOS:
        pending = tuple(i for i in target if i != anchor)
        for index, world in enumerate(relay.WORLDS):
            for actions, mass, cost, complete, quality, attempts in spell(target, anchor, world, pending, ()):
                paths[actions, round(cost, 6), complete, quality, attempts][index] += mass / len(relay.SCENARIOS)
    spell.cache_clear()
    width = max(len(row[0]) for row in paths)
    actions = np.array([ids + (-1,) * (width - len(ids)) for ids, *_ in paths])
    outcomes = np.array([row[1:] for row in paths], dtype=float)
    world_mass = np.stack(list(paths.values()))
    priors = {**relay.PRIORS, "design_mixture": relay.DESIGN}
    mass = {name: world_mass @ np.array([prior.get(world, 0) for world in relay.WORLDS])
            for name, prior in priors.items()}
    return states, actions, outcomes, mass


def normalize(logits, states):
    probabilities = np.ones_like(logits)
    for start, width in states.values():
        group = logits[start:start + width]
        exps = np.exp(group - max(group))
        probabilities[start:start + width] = exps / exps.sum()
    return probabilities


def evaluate(probabilities, actions, outcomes, mass):
    weights = probabilities[actions].prod(axis=1)
    results = {}
    for name, exogenous in mass.items():
        path_probability = weights * exogenous
        assert abs(path_probability.sum() - 1) < 1e-9
        cost, completion, score, attempts = path_probability @ outcomes
        results[name] = {"completion": completion, "final_record_score": score, "cost": cost,
                         "attempts": attempts, "record_reward": score - 35 - cost}
    return results


def fit(states, actions, outcomes, mass):
    logits = np.zeros(1 + sum(width for _, width in states.values()))
    momentum, square = np.zeros_like(logits), np.zeros_like(logits)
    responder = [start for state, (start, _) in states.items() if state[0] == "responder"]
    reward = outcomes[:, 2] - 35 - outcomes[:, 0]
    shifted = actions + 1
    history = []
    initial = normalize(logits, states)
    for step in range(STEPS + 1):
        p = normalize(logits, states)
        weighted = p[actions].prod(axis=1) * mass["design_mixture"]
        assert abs(weighted.sum() - 1) < 1e-9
        expected = weighted @ reward
        if step in (0, 30, 90, STEPS):
            history.append({"step": step, "record_reward": expected})
        if step == STEPS:
            break
        counts = np.bincount(shifted.ravel(), weights=np.repeat(weighted * (reward - expected), actions.shape[1]),
                             minlength=len(logits) + 1)[1:]
        gradient = np.zeros_like(logits)
        for start, width in states.values():
            group = slice(start, start + width)
            gradient[group] = counts[group] - counts[group].sum() * p[group]
        momentum = .9 * momentum + .1 * gradient
        square = .999 * square + .001 * gradient ** 2
        rate = LR * np.sqrt(1 - .999 ** (step + 1)) / (1 - .9 ** (step + 1))
        logits += rate * momentum / (np.sqrt(square) + 1e-8)

    swap = p.copy()
    peer_only = initial.copy()
    for start in responder:
        swap[start:start + 2] = (1., 0.)
        peer_only[start:start + 2] = p[start:start + 2]
    policies = {"initial_uniform": initial, "joint_learned": p,
                "learned_requester_canonical_responder": swap, "uniform_requester_learned_responder": peer_only}
    return history, policies


def scripted(states, policies, route):
    """Translate a dynamic-programming tree into the trajectory evaluator."""
    p = np.zeros_like(policies["joint_learned"])
    p[-1] = 1.
    trees = {(tuple(relay.KEYS.index(key) for key in case["target"]), relay.KEYS.index(case["anchor"])):
             case["policy"][route] for case in relay.run()["scenarios"]}
    for state, (start, _) in states.items():
        choice = 0
        if state[0] == "requester":
            _, target, anchor, history = state
            node = trees[target, anchor]
            for contact, seen in history:
                if node["action"] != "AB"[contact]:
                    node = {"action": "stop"}
                    break
                observed = "no_receipt" if seen is None else relay.KEYS[seen]
                node = node["on"].get(observed, {"action": "stop"})
            choice = ("stop", "A", "B").index(node["action"])
        p[start + choice] = 1.
    return p


if __name__ == "__main__":
    states, trajectories, outcomes, mass = build()
    history, policies = fit(states, trajectories, outcomes, mass)
    policies["exact_adaptive_canonical"] = scripted(states, policies, "3_record_adaptive")
    policies["exact_fixed_canonical"] = scripted(states, policies, "3_record_fixed")
    results = {name: evaluate(policy, trajectories, outcomes, mass) for name, policy in policies.items()}
    exact = relay.run()["averages"]
    for name, route in (("exact_adaptive_canonical", "3_record_adaptive"),
                        ("exact_fixed_canonical", "3_record_fixed")):
        for prior, expected in exact.items():
            for metric, value in results[name][prior].items():
                assert abs(value - expected[route][metric]) < 1e-7, (name, prior, metric)
    stress = {}
    for delivery in (.8, .95):
        stress_states, paths, values, priors = build(delivery)
        assert stress_states == states
        stress[str(delivery)] = {name: evaluate(policy, paths, values, priors)["design_mixture"]
                                 for name, policy in policies.items()}
    groups = {role: sum(state[0] == role for state in states) for role in ("requester", "responder")}
    p = policies["joint_learned"]
    policy = [{"local_state": state, "probabilities": p[start:start + width].tolist()}
              for state, (start, width) in states.items()]
    print(json.dumps({"steps": STEPS, "learning_rate": LR, "trajectory_rows": len(outcomes),
                      "state_counts": groups, "training": history, "metrics": results,
                      "changed_delivery_frozen_policies": stress, "policy": policy}, indent=2))
