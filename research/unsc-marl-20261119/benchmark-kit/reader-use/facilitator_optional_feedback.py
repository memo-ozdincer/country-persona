"""Jointly learn when a first transmission warrants a paid acknowledgment."""
from collections import Counter, defaultdict
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

import facilitator_feedback_cost as prior

base = prior.base
HERE = prior.HERE
ACK_FEE = base.FEE
BASELINE = HERE / "facilitator-feedback-cost-results.json"


def options(holding, mandatory):
    return (*product(holding, (True,) if mandatory else (False, True)), (base.PASS, False))


def episodes(reads, roster, first_weights, second_weights, mandatory, erase=False):
    for (left, right), availability in roster.items():
        first_state = "first", base.local(left, reads)
        for left_index, ((first, paid_ack), a) in enumerate(zip(options(left, mandatory), first_weights(first_state), strict=True)):
            for ok, ack, left_mass in base.events(first):
                signal = base.observation(first, reads, ack and paid_ack and not erase)
                second_state = "second", base.local(right, reads, signal)
                for right_index, (second, b) in enumerate(zip((*right, base.PASS), second_weights(second_state), strict=True)):
                    for received, right_mass in ((True, base.base.CHAIR), (False, 1 - base.base.CHAIR)):
                        mask = base.delivered(first, ok, second, received)
                        probability = availability * a * left_mass * b * right_mass
                        yield first_state, left_index, second_state, right_index, probability, mask, (
                            int(first is not None) + int(second is not None), int(paid_ack and ok), int(paid_ack and ack))


def synthetic():
    possible = tuple(product(base.RELATIONS, repeat=2))
    dispositions = {world: base.decision(world, base.TARGETS) for world in possible}
    counts = Counter(dispositions.values())
    return [(world, dispositions[world], 1 / (len(counts) * counts[dispositions[world]])) for world in possible]


def train_batch(mandatory):
    mapping = {}
    width = 0
    paths = defaultdict(float)
    first_n = 3 if mandatory else 5

    def slot(state, action, size):
        nonlocal width
        if state not in mapping:
            mapping[state] = width, size
            width += size
        return mapping[state][0] + action

    for reads, target, case_mass in synthetic():
        for first, a, second, b, p, mask, (payloads, acks, _) in episodes(
                reads, base.base.roster("training"), lambda _: (1.,) * first_n, lambda _: (1.,) * 3, mandatory):
            left = slot(first, a, first_n)
            right = slot(second, b, 3)
            cost = base.FEE * payloads + ACK_FEE * acks
            payoff = base.utility(base.decision(reads, mask), target)
            paths[left, right, cost, payoff] += case_mass * p
    return (mapping, np.array([(a, b) for a, b, _, _ in paths], dtype=int),
            np.array([(cost, 0., 35 + payoff, 0.) for _, _, cost, payoff in paths]),
            {"design_mixture": np.array(list(paths.values()))})


def profile(reads, roster, policy, outcomes, mandatory=False, erase=False):
    summary = Counter()
    total = 0.
    for _, _, _, _, p, mask, (payloads, acks, ack_deliveries) in episodes(
            reads, roster, policy.__getitem__, policy.__getitem__, mandatory, erase):
        total += p
        summary["payload_attempts"] += p * payloads
        summary["ack_attempts"] += p * acks
        summary["ack_deliveries"] += p * ack_deliveries
        summary.update({k: p * v for k, v in outcomes(mask).items()})
    assert abs(total - 1.) < 1e-9
    summary["net"] = summary["payoff"] - base.FEE * summary["payload_attempts"] - ACK_FEE * summary["ack_attempts"]
    return dict(summary)


def evaluate(scope, rows, roster, policy, mandatory):
    settled = prior.record.collect(row[1:] for row in rows if row[0] == scope)

    def payoff(case, mask):
        mark = case["receipts"][mask]
        action = mark["action"]
        return {"payoff": prior.record.rewards(mark)[1],
                "usable_retain": mark["strict"] and action == "retain",
                "usable_revise": mark["strict"] and action == "revise",
                "false_action": action != "withhold" and action != mark["expected"]}

    results = {}
    for erase in ((False,) if mandatory else (False, True)):
        detailed = {}
        for (panel, mode), item in settled.items():
            detailed[panel] = profile(item["reads"], roster, policy, lambda mask: payoff(item, mask), mandatory, erase)
        mean = {k: sum(row[k] for row in detailed.values()) / len(detailed) for k in next(iter(detailed.values()))}
        name = "mandatory_priced" if mandatory else "same_policy_ack_erased" if erase else "optional_ack"
        results[name] = {"mean": mean, "panels": detailed}
    return results


def train(mandatory):
    states, paths, outcomes, weights = train_batch(mandatory)
    optimizer = base.base.optimizer
    trace, fit = optimizer.fit(states, paths, outcomes, weights)
    model = base.base.observed_weights(states, fit["joint_learned"])
    training = sum(mass * profile(reads, base.base.roster("training"), model,
                                 lambda mask: {"payoff": base.utility(base.decision(reads, mask), truth)},
                                 mandatory)["net"]
                   for reads, truth, mass in synthetic())
    assert abs(training - trace[-1]["record_reward"]) < 1e-9
    return model, {"states": len(states), "trajectory_rows": len(paths), "training_trace": trace}


def run():
    optional, optional_fit = train(False)
    mandatory, mandatory_fit = train(True)
    archived = prior.dev.load(BASELINE)["evaluations"]
    rows = list(prior.cases())
    evaluated = {}
    for scope in ("development", "transfer"):
        evaluated[scope] = {}
        for inventory in ("split", "overlap"):
            roster = base.base.roster(inventory)
            stats = evaluate(scope, rows, roster, optional, False) | evaluate(scope, rows, roster, mandatory, True)
            for system, data in archived[scope][inventory]["systems"].items():
                m = data["mean"]
                stats[system] = {"mean": {
                    "net": m["brief_payoff"] - base.FEE * m["payload_attempts"] - ACK_FEE * m["ack_attempts"],
                    **{k: m[k] for k in ("usable_retain", "usable_revise", "false_action", "payload_attempts", "ack_attempts")},
                }}
            evaluated[scope][inventory] = stats
    return {"scope": "Two exact joint fits on the same synthetic relation pairs and send fees. The optional actor "
                     "can decline acknowledgment and the mandatory arm is repriced during training too. "
                     "The second actor sees either the delivered acknowledgment or silence. Archived language cases "
                     "and grades are used only in transfer evaluation. No LLM updates.",
            "payload_fee": base.FEE, "ack_attempt_fee": ACK_FEE, "updates_per_fit": base.base.optimizer.STEPS,
            "traces": {"optional": optional_fit, "mandatory_priced": mandatory_fit}, "evaluations": evaluated,
            "policies": {key: [{"state": k, "probabilities": v} for k, v in model.items()]
                         for key, model in (("optional", optional), ("mandatory_priced", mandatory))},
            "file_sha256": {p.name: sha256(p.read_bytes()).hexdigest()
                            for p in (Path(__file__), Path(prior.__file__), BASELINE)}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
