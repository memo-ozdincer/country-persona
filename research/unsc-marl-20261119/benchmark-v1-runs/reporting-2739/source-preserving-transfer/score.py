"""Score the paired, partial and crossed comparisons using the existing rubric."""
import json

from study import CARDS, CASE, HERE, ORDERS, base

ANCHOR = base.read(HERE.parent / "anchor.json")
PUBLIC = (
    "The Council adopted Japanese–US draft S/2024/500 as resolution 2739 (2024), 12–0–3. "
    "Algeria, China and Russia abstained. It extended the Secretary-General’s reporting request "
    "under paragraph 10 of resolution 2722 (2024) through 15 January 2025, without granting "
    "new authority for military action."
)
SPONSORS = "Japan and the United States wanted accurate, timely information about the attacks for Council deliberations."
ALGERIA = (
    "Algeria valued monthly reporting on attacks on merchant and commercial vessels to keep the Council informed. "
    "It abstained over implementation of resolution 2722 and alleged misuse or misinterpretation of self-defence "
    "through attacks on sovereign territory."
)


def assemble(receipts):
    assert ANCHOR["packet"]["answer"].startswith(PUBLIC + " " + SPONSORS)
    prior_text = (HERE.parent / "correction-bank/chair-scope/source_bound.py").read_text()
    assert 'Algeria valued monthly reporting on attacks on merchant and commercial vessels to keep the Council informed. ' in prior_text
    assert 'It abstained over implementation of resolution 2722 and alleged misuse or misinterpretation of self-defence through attacks on sovereign territory.' in prior_text
    return " ".join([PUBLIC] + ([SPONSORS] if "sponsors" in receipts else [])
                    + ([ALGERIA] if "algeria" in receipts else []))


def citations(*ids):
    return [{"block": id_, "quote": CARDS[id_]} for id_ in ids]


def score():
    judge = base.anchor.scorer()
    archive = base.read(HERE / "verified.json")["outputs"]
    marks = base.read(HERE / "marks.json")
    assert archive.keys() == marks.keys() == ORDERS.keys()
    output = {}
    core = {"disposition", "draft-and-sponsors", "operative-report", "authority"}
    anchor_units = {row["id"]: row for row in ANCHOR["verdict"]["units"]}
    specs = {row["id"]: row for row in CASE["rubric"]}
    assert set(anchor_units) == set(specs)
    assert ANCHOR["score"]["released_70"] == 70
    for name, receipts in ORDERS.items():
        visible = {"vote", "action", *receipts}
        is_pair = {"sponsors", "algeria"} <= visible
        packet = {
            **ANCHOR["packet"], "id": name, "answer": assemble(receipts),
            "evidence": [{"id": id_, "text": text} for id_, text in CARDS.items() if id_ in visible],
        }
        units = {key: anchor_units[key] if key in core else {
            "id": key, "status": "unmet", "source": [], "response": "",
            "reason": "No warranted comparison or standalone statement for this criterion is present."
        } for key in specs}
        if "sponsors" in receipts:
            units["sponsor-reason"] = {"id": "sponsor-reason", "status": "met", "source": citations("sponsors"),
                                       "response": SPONSORS, "reason": specs["sponsor-reason"]["rule"]}
        if "algeria" in receipts:
            units["algeria-reason"] = {"id": "algeria-reason", "status": "met", "source": citations("algeria"),
                                       "response": ALGERIA, "reason": specs["algeria-reason"]["rule"]}
        guard = {"status": "clear", "source": [], "response": "", "reason": "The fixed facts are source grounded."}
        standalone = judge.score(packet, {"id": name, "units": list(units.values()), "guard": guard})["final"]["lower"]
        assert standalone == 42 + 7 * len({"sponsors", "algeria"} & set(receipts))
        response = archive[name]
        comparison = response["text"]
        abstained = comparison == "NONE"
        mark = marks[name]
        units["bounded-overlap"] = mark["overlap"]
        assert mark["overlap"]["status"] != "met" or (is_pair and not abstained)
        if not abstained:
            packet["answer"] += " " + comparison
        result = judge.score(packet, {"id": name, "units": list(units.values()), "guard": mark["guard"]})
        word_count = len(packet["answer"].split())
        blockers = []
        if result["guard"] != "clear":
            blockers.append("guard_" + result["guard"])
        if word_count > CASE["word_cap"] or (not abstained and not 0 < len(comparison.split()) <= 38):
            blockers.append("word_cap")
        if response["termination"] != "complete":
            blockers.append("incomplete")
        if len(receipts) < 2 and not abstained:
            blockers.append("expected_abstention")
        native = result["final"]["lower"] if not blockers else 0
        output[name] = {
            "receipts": receipts, "comparison": comparison, "record": packet["answer"],
            "words": word_count, "abstained": abstained, "standalone": standalone,
            "raw": result["final"], "always_call": native, "known_pair": native if is_pair else standalone,
            "authored_ceiling": standalone + (14 if is_pair else 0), "blockers": blockers,
        }
    full_orders = ("algeria-first", "sponsors-first")
    pair_gain = {key: output[key]["known_pair"] - output[key]["standalone"] for key in full_orders}
    return {"outcomes": output, "pair_gain": pair_gain}


if __name__ == "__main__":
    print(json.dumps(score(), ensure_ascii=False, indent=2))
