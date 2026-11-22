"""Test delivery acknowledgments against planned sends using a strict two-field handoff."""
import argparse
from collections import defaultdict
from itertools import product
import json
from pathlib import Path

import numpy as np

import payload_policy as base

HERE = Path(__file__).resolve().parent
UNAMI = HERE.parent / "colombia2023/unami-verbatim.json"
OLD = HERE / "evidence/payload-policy.json"
AWARD = 28.
# The first transmission must actually reach the chair for an acknowledgment.
# Publish the acknowledgment over the same 80% side channel as planned sends.
MODES = ("ack", "plan", "silent")
OPENINGS = tuple(product((0, 1), repeat=len(base.PAIRS)))


def events(first, mode, link):
    for delivered, p in ((False, 1 - link), (True, link)):
        sent = mode == "plan" or (mode == "ack" and delivered)
        if sent:
            yield delivered, first, p * base.PEER
            yield delivered, None, p * (1 - base.PEER)
        else:
            yield delivered, None, p


def successful(first, delivered, second, required):
    return delivered and first != second and frozenset((first, second)) == frozenset(required)


def paths():
    states, weights = {}, defaultdict(float)
    dim = 0

    def action(state, choice):
        nonlocal dim
        if state not in states:
            states[state] = dim, 2
            dim += 2
        return states[state][0] + choice

    for focus in base.PAIRS:
        for (left, right), world_p in base.roster("training").items():
            for i, first in enumerate(left):
                a = action(("sender", focus, left), i)
                for delivered, obs, prob in events(first, "ack", base.CHAIR):
                    for j, second in enumerate(right):
                        b = action(("recipient", focus, right, obs), j)
                        completed = base.CHAIR * successful(first, delivered, second, focus)
                        weights[a, b, completed] += world_p * prob / len(base.PAIRS)
    actions = np.array([(a, b) for a, b, _ in weights], dtype=int)
    outcomes = np.array([(0., done, 35 + AWARD * done, 2.) for _, _, done in weights])
    return states, actions, outcomes, {"design_mixture": np.array(list(weights.values()))}


def exact(focus, prior, mode, link):
    best, policy = -1., None
    for code in OPENINGS:
        left_choice = dict(zip(base.PAIRS, code, strict=True))
        values = defaultdict(lambda: [0., 0.])
        for (left, right), p in prior.items():
            first = left[left_choice[left]]
            for delivered, seen, chance in events(first, mode, link):
                for j, second in enumerate(right):
                    values[right, seen][j] += p * chance * link * successful(first, delivered, second, focus)
        score = sum(max(v) for v in values.values())
        if score > best + 1e-12:
            best = score
            policy = {("sender", focus, left): (1. - i, float(i)) for left, i in left_choice.items()}
            for (right, seen), value in values.items():
                pick = int(value[1] > value[0] + 1e-12)
                policy["recipient", focus, right, seen] = (1. - pick, float(pick))
    return best, policy


def packet_replay(weights, focus, prior, mode, link, score_table, mask=False):
    metrics = defaultdict(float)
    metrics["side_channel_attempt_rate"] = {"ack": link, "plan": 1., "silent": 0.}[mode]
    receipts = defaultdict(float)
    for (left, right), p in prior.items():
        for first, a in base.choose_probability(weights, "sender", focus, left):
            if not a:
                continue
            for delivered, seen, obs_p in events(first, mode, link):
                if not obs_p:
                    continue
                observed = None if mask else seen
                for second, b in base.choose_probability(weights, "recipient", focus, right, observed):
                    weight = p * a * obs_p * b
                    metrics["visible_peer_rate"] += weight * (seen is not None and not mask)
                    metrics["duplicate_attempt_rate"] += weight * (first == second)
                    for second_ok, prob in ((False, 1 - link), (True, link)):
                        held = frozenset(i for i, received in ((first, delivered), (second, second_ok)) if received)
                        receipts[held] += weight * prob
    assert abs(sum(receipts.values()) - 1) < 1e-9
    targets = set(focus)
    for delivered, weight in receipts.items():
        seen = delivered & targets
        metrics["requested_received"] += weight * len(seen)
        metrics["complete_handoff"] += weight * (seen == targets)
        if score_table is not None:
            ask = focus[0] in seen
            fetch = focus[1] in seen
            key = f"{'ask' if ask else 'pass'}/{'fetch' if fetch else 'no_fetch'}"
            row = score_table[key]
            assert row["both_obligations_source_complete"] == (seen == targets)
            metrics["record_score"] += weight * row["points"]
            metrics["usable_calendar"] += weight * (row["calendar_entries"] == 3)
    return dict(metrics)


def stored(path):
    def freeze(item):
        return tuple(map(freeze, item)) if isinstance(item, list) else item
    return {freeze(r["state"]): r["probabilities"] for r in json.loads(path.read_text())["policy"]}


def headroom():
    result = {}
    for label in ("training", "overlap", "split"):
        prior = base.roster(label)
        result[label] = {mode: sum(exact(f, prior, mode, base.CHAIR)[0] for f in base.PAIRS) / len(base.PAIRS)
                         for mode in MODES}
    return result


def run():
    head = headroom()
    states, actions, terminal, weights = paths()
    history, fit = base.optimizer.fit(states, actions, terminal, weights)
    learned = base.observed_weights(states, fit["joint_learned"])
    older = stored(OLD)
    receipts = json.loads(UNAMI.read_text())["records"]["no_question"]["receipts"]
    results = {}
    for label in ("training", "overlap", "split"):
        for link in (base.CHAIR, .7):
            prior = base.roster(label)
            rows = []
            for focus in base.PAIRS:
                exacts = {mode: exact(focus, prior, mode, link) for mode in MODES}
                variants = {"trained_ack": (learned, "ack", False),
                            "trained_with_plan": (learned, "plan", False),
                            "trained_ack_erased": (learned, "ack", True),
                            "older_raw_plan": (older, "plan", False),
                            "older_raw_ack": (older, "ack", False)}
                variants.update({f"exact_{mode}": (policy, mode, False) for mode, (_, policy) in exacts.items()})
                read = {name: packet_replay(policy, focus, prior, mode, link, receipts, mask)
                        for name, (policy, mode, mask) in variants.items()}
                for name, (expected, _) in exacts.items():
                    assert abs(read[f"exact_{name}"]["complete_handoff"] - expected) < 1e-9
                assert read["trained_ack"]["complete_handoff"] <= exacts["ack"][0] + 1e-9
                assert abs(read["trained_ack"]["complete_handoff"]
                           - read["trained_with_plan"]["complete_handoff"]) < 1e-9
                assert abs(exacts["ack"][0] - exacts["plan"][0]) < 1e-9
                rows.append(read)
            results[f"{label}/{link}"] = {name: {key: sum(row[name][key] for row in rows) / len(rows)
                                                  for key in metrics}
                                           for name, metrics in rows[0].items()}
    actual = results[f"training/{base.CHAIR}"]["trained_ack"]["complete_handoff"] * AWARD
    assert abs(actual - history[-1]["record_reward"]) < 1e-9
    return {"scope": "One small exact policy-gradient fit on abstract public focus pairs with uniform private rosters. "
                     "UNAMI held-out documentary outcomes come from the fixed no-question remainder and two pre-reviewed clauses. "
                     "Two irrelevant roster slots consume choices and carry no scored UNAMI text. No model generation or open-ended negotiation.",
            "initial_headroom": head, "updates": base.optimizer.STEPS, "training": history,
            "states": len(states), "traces": len(actions), "test": results,
            "pins": {str(p.resolve().relative_to(HERE.parent)): base.channel.runner.digest(p)
                     for p in (Path(__file__), Path(base.__file__), Path(base.optimizer.__file__), OLD, UNAMI)},
            "policy": [{"state": state, "probabilities": p} for state, p in learned.items()]}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--headroom", action="store_true")
    args = cli.parse_args()
    print(json.dumps(headroom() if args.headroom else run(), indent=2))
