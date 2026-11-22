"""Train with uncertain desk hints and test frozen policies on four UN dockets."""
from functools import partial
import json
from pathlib import Path
from unittest.mock import patch

import receipt_feedback as protocol
from receipt_feedback_transfer import metrics as authored_metrics

HERE = Path(__file__).resolve().parent
results = protocol.results
policy = protocol.policy
relay = protocol.relay
shift = protocol.shift
optimizer = protocol.optimizer
HINT_RELIABILITY = .75
TRUE_SPECIALIST = 1
distribution = shift.distribution


def mix(correct, wrong, reliability):
    assert correct.keys() == wrong.keys()
    return {world: reliability * p + (1 - reliability) * wrong[world] for world, p in correct.items()}


def uncertain(pending, strength, hint):
    return mix(distribution(pending, strength, hint), distribution(pending, strength, 1 - hint), HINT_RELIABILITY)


def snapshot(path):
    return {shift.transfer.immutable(row["local_state"]): row["probabilities"]
            for row in results.load(path)["policy"]}


def training():
    with patch.object(shift, "distribution", uncertain):
        states, actions, outcomes, exogenous = protocol.train_paths()
    history, probabilities = optimizer.fit(states, actions, outcomes, exogenous)
    weights = {key: probabilities["joint_learned"][offset:offset + size].tolist()
               for key, (offset, size) in states.items()}
    scores = optimizer.scores()
    net = 0.
    for target, anchor in relay.SCENARIOS:
        prior = uncertain(set(target) - {anchor}, shift.TRAIN_STRENGTH, 0)
        routed = protocol.replay(weights, target, anchor, prior)
        assert abs(sum(p for p, _, _ in routed.values()) - 1) < 1e-9
        net += sum(p * (scores[target, anchor, tuple(sorted(left))] - 35) - fee
                   for left, (p, fee, _) in routed.items())
    assert abs(net / len(relay.SCENARIOS) - history[-1]["record_reward"]) < 1e-9
    return history, weights, len(actions)


def route(weights, prior, target, anchor, context, hint, blind=False):
    with patch.object(shift.transfer, "outcomes", partial(protocol.replay, blind=blind)):
        return shift.remap(weights, prior, target, anchor, context, (hint, 1 - hint))


def mix_routes(a, b, reliability):
    # A randomized choice of nominal specialist is made once per episode.
    return {left: tuple(reliability * x + (1 - reliability) * y
                        for x, y in zip(a.get(left, (0.,) * 3), b.get(left, (0.,) * 3), strict=True))
            for left in a.keys() | b.keys()}


def datasets():
    for family, ids, bank, mapping in shift.datasets():
        def review(target, anchor, routes, ids=ids, bank=bank):
            return authored_metrics(routes, set(target) - {anchor}, target, ids, bank, anchor)
        yield family, ids, bank, mapping, review

    source = results.load(results.EVIDENCE / "policy-replay.json")
    generated = results.load(results.EVIDENCE / "results.json")["field_packets"]
    case = results.load(results.writer.CASE)
    ids = tuple(case["sources"])
    bank = results.verified_bank(case)

    def drc(target, anchor, routes):
        out = {name: policy.benefits(target, anchor, ids, trace, generated, bank)
               for name, trace in routes.items()}
        return {name: {"net": score["actual_net_gain"], "complete": score["required_source_completion"],
                       "record_points": score["actual_points"], "contact_fees": score["source_cost"],
                       "contact_attempts": score["contacts"], "authored_net": score["authored_net_gain"]}
                for name, score in out.items()}

    yield "drc_generated", ids, bank, source["table_alignment"], drc


def run():
    history, fitted, rows_fit = training()
    parent = HERE / "evidence/receipt-feedback.json"
    original = snapshot(parent)
    assert original.keys() == fitted.keys()
    families = {}
    for family, ids, bank, mapping, review in datasets():
        table = {(row["anchor"], *row["other_cards"]): row for row in mapping["rows"]}
        case_rows = []
        for target, anchor in relay.SCENARIOS:
            pending = tuple(i for i in target if i != anchor)
            context = table[ids[anchor], *(ids[i] for i in pending)]
            prior = distribution(pending, 6., TRUE_SPECIALIST)
            oracle = {}
            with patch.object(relay, "transitions", protocol.script_transitions):
                oracle["oracle_adaptive"] = policy.script(target, anchor, ids, bank, prior, True)
                oracle["oracle_fixed"] = policy.script(target, anchor, ids, bank, prior, False)
                mixed_prior = uncertain(pending, 6., TRUE_SPECIALIST)
                calibrated = policy.script(target, anchor, ids, bank, mixed_prior, True)
            routes = {"correct_hint": {}, "wrong_hint": {}}
            for condition, hint in (("correct_hint", TRUE_SPECIALIST), ("wrong_hint", 1 - TRUE_SPECIALIST)):
                routes[condition] = {
                    "always_correct_fit": route(original, prior, target, anchor, context, hint),
                    "uncertain_hint_fit": route(fitted, prior, target, anchor, context, hint),
                    "uncertain_fit_receipt_erased": route(fitted, prior, target, anchor, context, hint, True),
                }

            old_without_hint = mix_routes(routes["correct_hint"]["always_correct_fit"],
                                          routes["wrong_hint"]["always_correct_fit"], .5)
            physical = {}
            for level, routed in routes.items():
                physical[level] = review(target, anchor, {**oracle, **routed,
                                                          "old_fit_random_hint": old_without_hint})
            uncertain_roster = {name: mix_routes(routed, routes["wrong_hint"][name], HINT_RELIABILITY)
                                for name, routed in routes["correct_hint"].items()}
            physical["hint_reliability_75"] = review(target, anchor, {**oracle, **uncertain_roster,
                                                                    "old_fit_random_hint": old_without_hint,
                                                                    "calibrated_adaptive": calibrated})
            if family != "drc_generated":
                mix_scores = physical["hint_reliability_75"]
                assert mix_scores["calibrated_adaptive"]["net"] + 1e-9 >= mix_scores["uncertain_hint_fit"]["net"]
            case_rows.append({"target": [ids[i] for i in target], "anchor": ids[anchor], "values": physical})

        families[family] = {"mean": {level: shift.transfer.mean([r["values"][level] for r in case_rows])
                                     for level in ("correct_hint", "wrong_hint", "hint_reliability_75")},
                            "rows": case_rows}
    return {"scope": "One joint fit on written-vote evidence with a 75% reliable specialist hint. "
                     "The calibrated adaptive script knows the mixture, while oracle scripts know the actual "
                     "prior for each evaluated hint condition. The pure-condition scores hold the policy fixed. "
                     "The mixed learned and calibrated script scores use the desk-symmetric weighted prior.",
            "fit_hint_reliability": HINT_RELIABILITY, "steps": optimizer.STEPS, "trajectory_rows": rows_fit,
            "training": history, "families": families,
            "policy": [{"local_state": key, "probabilities": prob} for key, prob in fitted.items()],
            "pins": {p.name: results.writer.runner.digest(p) for p in (
                Path(__file__), Path(protocol.__file__), parent, results.EVIDENCE / "results.json")}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
