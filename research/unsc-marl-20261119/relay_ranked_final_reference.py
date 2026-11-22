"""Compile a comparison memo directly from the delivered ranked packet."""
from hashlib import sha256
import json

from relay_ranked_final import suite
from relay_compromise_audit import oracle


def grade_group(card):
    return ", ".join(f"{package}={grade}" for package, grade in card["grades"].items())


def status_sentences(packet):
    status = packet["checked_status"]
    cards = packet["received_cards"]
    if status == "UNRESOLVED":
        assert len(cards) == 1
        missing, = set(packet["possible_card_holders"]) - {c["owner"] for c in cards}
        return (f"{cards[0]['owner']} submitted {grade_group(cards[0])}. "
                f"Request the missing card from the {missing} to determine whether there is an overlap.")
    first, second = cards
    left, right = first["grades"], second["grades"]
    names = sorted(set(left) | set(right))
    best = oracle(names, [left.get(k, 0) for k in names], [right.get(k, 0) for k in names])
    reason = "provisionally" if first["verification"] == "reported" else "for this exercise"
    qualifier = "reported, unverified" if first["verification"] == "reported" else "verified"
    claims = f"{first['owner']} ({qualifier}) submitted {grade_group(first)}. {second['owner']} submitted {grade_group(second)}."
    if status == "IMPASSE":
        assert best == {"impasse"} and not set(left) & set(right)
        return f"{claims} The acceptable sets are disjoint. Refer the impasse {reason} for further discussion."
    assert status in best
    alternative = next(iter(sorted(best - {status})), None)
    if alternative is None:
        alternative = next(iter(sorted(set(left) & set(right) - {status})))
    def payoff(k):
        return min(left[k], right[k]), left[k] + right[k]
    comparison = "ties" if payoff(status) == payoff(alternative) else "outranks"
    return (f"{claims} Recommend {status} {reason}. Its lower grade and sum {payoff(status)} "
            f"{comparison} {alternative} {payoff(alternative)}.")


def record(prompt):
    packet = prompt["expected"]
    sentences = [status_sentences(packet)]
    correction = packet["correction"]
    if correction:
        assert correction["grade"] == packet["received_cards"][0]["grades"][correction["package"]]
        sentences.append(f"The {correction['owner']} clarified that {correction['package']} is a fallback (grade {correction['grade']}).")
    sentences.append("The workshop has no official authority.")
    sentences.extend(f"{x['label']}: {x['quote']}" for x in packet["historical_evidence"])
    result = "Workshop status: " + packet["checked_status"] + "\n" + " ".join(sentences)
    assert len(result.split()) <= 120
    for fact in packet["historical_evidence"]:
        assert fact["quote"] in result
    return {"id": prompt["id"], "record": result, "words": len(result.split()),
            "dossier_sha256": sha256(prompt["messages"][-1]["content"].encode()).hexdigest()}


if __name__ == "__main__":
    print(json.dumps([record(prompt) for prompt in suite()], indent=2))
