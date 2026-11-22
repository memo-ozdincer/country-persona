"""Score the native append and read out matched message contribution."""
import json

from study import CASE, HERE, ORDERS, anchor, read

FULL = ("safeguards-first", "india-first")
BASELINES = {
    "none": ("literal", 30),
    "safeguards": ("without-india", 48),
    "india": ("without-safeguards", 40),
    **{order: ("literal", 58) for order in FULL},
}


def score():
    evidence = read(HERE / "verified.json")
    annotations = read(HERE / "marks.json")
    assert annotations.keys() == evidence["outputs"].keys() == ORDERS.keys()
    anchors = read(HERE.parent / "anchors.json")
    scorer = anchor.scorer()
    cases = {}
    for name, receipts in ORDERS.items():
        retrieved = set(receipts) | {"vote", "scope"}
        base_key, expected = BASELINES[name]
        base = anchors[base_key]
        packet = {
            **base["packet"], "id": name,
            "evidence": [item for item in base["packet"]["evidence"] if item["id"] in retrieved],
            "answer": base["packet"]["answer"] if receipts else " ".join(anchor.BASE),
        }
        verdict = {
            "id": name, "guard": base["verdict"]["guard"],
            "units": [mark if all(src["block"] in retrieved for src in mark["source"]) else {
                **mark, "status": "unmet", "response": "", "source": [],
                "reason": "The source did not arrive and this standalone fact was left out."
            } for mark in base["verdict"]["units"]],
        }
        standalone = scorer.score(packet, verdict)["final"]["lower"]
        assert standalone == expected and len(packet["answer"].split()) <= CASE["word_cap"]
        reply = evidence["outputs"][name]
        sentence = reply["text"]
        mark = annotations[name]
        blockers = []
        abstained = sentence == "NONE"
        if reply["termination"] != "complete":
            blockers.append("incomplete")
        if not abstained:
            if len(receipts) < 2:
                blockers.append("expected_abstention")
            if not 0 < len(sentence.split()) <= 38:
                blockers.append("comparison_word_count")
            packet["answer"] += " " + sentence
            if len(packet["answer"].split()) > CASE["word_cap"]:
                blockers.append("final_word_count")
        assert not abstained or (mark["relation"]["status"] == "unmet" and mark["guard"]["status"] == "clear")
        assert len(receipts) == 2 or mark["relation"]["status"] != "met"
        same_units = [mark["relation"] if unit["id"] == "relation" else unit for unit in verdict["units"]]
        verdict = {"id": name, "units": same_units, "guard": mark["guard"]}
        grade = scorer.score(packet, verdict)
        if grade["guard"] != "clear":
            blockers.append("guard_" + grade["guard"])
        native = grade["final"]["lower"] if not blockers else 0
        cases[name] = {
            "receipts": receipts, "brief": packet["answer"], "comparison": sentence,
            "abstained": abstained, "comparison_words": 0 if abstained else len(sentence.split()),
            "input_tokens": reply["input_tokens"], "output_tokens": reply["output_tokens"],
            "standalone": standalone, "raw_70": grade["final"], "always_call": native,
            "require_both": native if len(receipts) == 2 else standalone,
            "authored_ceiling": standalone + (12 if len(receipts) == 2 else 0),
            "blockers": blockers,
        }
    credit = {}
    for policy in ("standalone", "always_call", "require_both", "authored_ceiling"):
        credit[policy] = {}
        for order in FULL:
            both, adopted, india, empty = (cases[row][policy] for row in (order, "safeguards", "india", "none"))
            credit[policy][order] = {
                "safeguards_leave_one_out": both - india, "india_leave_one_out": both - adopted,
                "joint_beyond_standalone_contributions": both - adopted - india + empty,
            }
    # Illustrative independent delivery at p=.75 with the two display orders balanced.
    expected = {}
    p = 0.75
    for policy in credit:
        both = sum(cases[order][policy] for order in FULL) / len(FULL)
        single = cases["safeguards"][policy] + cases["india"][policy]
        expected[policy] = (1 - p)**2 * cases["none"][policy] + p * (1 - p) * single + p**2 * both
    return {"cases": cases, "message_credit": credit, "release_at_independent_p75": expected}


if __name__ == "__main__":
    print(json.dumps(score(), ensure_ascii=False, indent=2))
