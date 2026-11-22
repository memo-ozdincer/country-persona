"""Locate the unreliable-hint transfer tradeoff with frozen policy swaps."""
import json

import receipt_hint_fit as fit


def run():
    evidence = fit.HERE / "evidence"
    previous = fit.snapshot(evidence / "receipt-feedback.json")
    uncertain = fit.snapshot(evidence / "receipt-hint-fit.json")
    rows = fit.results.load(evidence / "receipt-hint-fit.json")["families"]["drc_generated"]["rows"]
    original_opening = {key for key in previous if key[0] == "requester" and not key[3]}
    chair = {key for key in previous if key[0] == "requester"}
    assert len(original_opening) == len(fit.relay.SCENARIOS) == 12
    variants = {
        "previous_fit": previous,
        "uncertain_fit": uncertain,
        "uncertain_opening_only": {key: uncertain[key] if key in original_opening else p
                                   for key, p in previous.items()},
        "uncertain_followup_only": {key: uncertain[key] if key in chair - original_opening else p
                                    for key, p in previous.items()},
        "uncertain_responder_only": {key: uncertain[key] if key not in chair else p
                                     for key, p in previous.items()},
    }
    _, ids, _, mapping, review = next(row for row in fit.datasets() if row[0] == "drc_generated")
    map_rows = {(r["anchor"], *r["other_cards"]): r for r in mapping["rows"]}
    regimes = {"correct": [], "wrong": [], "reliable_75": []}
    for (target, anchor), archived in zip(fit.relay.SCENARIOS, rows, strict=True):
        pending = tuple(i for i in target if i != anchor)
        context = map_rows[ids[anchor], *(ids[i] for i in pending)]
        true = fit.TRUE_SPECIALIST
        prior = fit.distribution(pending, 6., true)
        observed = {mode: {name: fit.route(weights, prior, target, anchor, context, hint)
                           for name, weights in variants.items()} for mode, hint in (
                               ("correct", true), ("wrong", 1 - true))}
        observed["reliable_75"] = {
            name: fit.mix_routes(routed, observed["wrong"][name], fit.HINT_RELIABILITY)
            for name, routed in observed["correct"].items()}
        for mode, metrics in regimes.items():
            values = review(target, anchor, observed[mode])
            label = {"correct": "correct_hint", "wrong": "wrong_hint",
                     "reliable_75": "hint_reliability_75"}[mode]
            for variant, baseline in (("previous_fit", "always_correct_fit"),
                                      ("uncertain_fit", "uncertain_hint_fit")):
                assert abs(values[variant]["net"] - archived["values"][label][baseline]["net"]) < 1e-9
            metrics.append(values)

    return {
        "scope": "Posthoc swaps of frozen probabilities on the generated DRC docket, with the same "
                 "alignment and paid replies. Nothing is fitted or selected for deployment here.",
        "opening_probabilities": {
            name: [sum(weights[key][action] for key in sorted(original_opening)) / len(original_opening)
                   for action in range(3)] for name, weights in variants.items()},
        "opening_action_order": ["stop", "hinted_desk", "other_desk"],
        "means": {key: fit.shift.transfer.mean(values) for key, values in regimes.items()},
        "rows": regimes,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
