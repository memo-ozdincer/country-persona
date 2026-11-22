"""Compile exact decision records that trace the grade elicited by clarification."""
import json
from itertools import product

import three_seat_followup as experiment

base = experiment.base
NAMES = ("first delegate", "second delegate", "public seat")


def ordered_values(world):
    cards = (base.CARDS_A[world[0]], base.CARDS_B[world[1]], base.PUBLIC)
    return {package: {"minimum": min(grades), "total": sum(grades),
                      "zero_seats": [seat for seat, grade in zip(NAMES, grades, strict=True) if grade == 0]}
            for package, grades in zip(base.PACKAGES, zip(*cards, strict=True), strict=True)}


def verdict(worlds, warranted):
    if not warranted:
        contrast = {}
        order = (*base.PACKAGES, "impasse")
        for option in order:
            counter = next((world for world in worlds if option not in base.TRUTH[world]), None)
            assert counter is not None
            contrast[option] = {"compatible_world": counter, "winners": sorted(base.TRUTH[counter])}
        return {"decision": "unresolved", "excluded_universal_choices": contrast}
    return {"decision": sorted(warranted)[0], "acceptable_decisions": sorted(warranted),
            "proof": [{"compatible_world": world, "scores": ordered_values(world),
                       "winners": sorted(base.TRUTH[world])} for world in worlds]}


def describe(receipts):
    return [{"delegate": NAMES[seat], "package": base.PACKAGES[seen[0]], "grade": seen[1]}
            for seat, seen in enumerate(receipts) if seen is not None]


def format_question(q):
    return {"delegate": NAMES[q[0]], "package": base.PACKAGES[q[1]],
            "text": f"What is your grade for package {base.PACKAGES[q[1]]}?"}


def contrast(world, first, second, query):
    receipts = (base.message(world, 0, first), base.message(world, 1, second))
    options, warranted = base.verify(*receipts)
    assert not warranted and query in experiment.actions(receipts)
    answer = base.message(world, *query)[1]
    remaining, verified = experiment.next_evidence(receipts, query, answer)
    assert world in remaining and verified <= base.TRUTH[world] and verified
    return {
        "initial_receipts": describe(receipts),
        "before_or_if_reply_lost": verdict(options, warranted),
        "question": format_question(query),
        "verified_reply": {"speaker": NAMES[query[0]], "package": base.PACKAGES[query[1]], "grade": answer},
        "after_successful_reply": verdict(remaining, verified),
    }


def run():
    # Both truth worlds produce identical opening evidence.
    to_d = contrast((1, 0), 0, 2, (1, 0))
    to_a = contrast((1, 2), 0, 2, (1, 0))
    assert to_d["initial_receipts"] == to_a["initial_receipts"]
    assert to_d["before_or_if_reply_lost"] == to_a["before_or_if_reply_lost"]
    assert to_d["question"] == to_a["question"]
    assert to_d["after_successful_reply"]["decision"] == "D" and to_a["after_successful_reply"]["decision"] == "A"
    tally = experiment.capacity()
    assert sum(bool(row["sufficient_opening_pairs"]) for row in tally) == 8
    assert all(row["sufficient_opening_pairs"] or row["newly_sufficient_examples"] for row in tally)
    world = (1, 2)
    ceiling = max(
        sum(mass * max(experiment.q_gain(world, shown, q) for q in experiment.actions(shown))
            for mass, shown, _, _ in base.decisions(base.message(world, 0, i), base.message(world, 1, j)))
        for i, j in product(range(len(base.PACKAGES)), repeat=2)
    )
    assert abs(ceiling - base.DELIVER ** 2 * experiment.REPLY) < 1e-12
    return {"scope": "Deterministic records for two fictional worlds that share the same initial evidence, "
                     "using only visible receipts and completions. Missing replies preserve the earlier result.",
            "followup_leads_to_D": to_d, "followup_leads_to_A": to_a,
            "structurally_hard_world": world, "clairvoyant_query_certification_ceiling": ceiling}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
