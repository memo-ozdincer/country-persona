"""Score all receipts and compare role presence to exact relation-specific cards."""
import json

from concern_study import CARDS, CASE, HERE, OWNERS, POSITIVE, RELEASE, VIEWS, earlier, native_sentence, read

judge = earlier.previous.load("concern_judge", RELEASE / "judge_score.py")
PUBLIC = tuple(row["id"] for row in CASE["public"])
RUBRIC = {row["id"]: row for row in CASE["rubric"]}


def citation(keys):
    return [{"block": key, "quote": CARDS[key]} for key in keys]


def fixed_packet(name, ids):
    visible = (*PUBLIC, *ids)
    packet = {
        "id": name, "mode": "FINAL", "task": CASE["task"], "rubric": CASE["rubric"],
        "answer": "\n\n".join(CARDS[key] for key in visible),
        "evidence": [{"id": key, "text": CARDS[key]} for key in visible],
    }
    units = [
        {"id": key, "status": "met", "source": citation([key]),
         "response": CARDS[key], "reason": "The fixed record retains the archived source card."}
        if key in visible else
        {"id": key, "status": "unmet", "source": [], "response": "",
         "reason": "The relevant standalone or comparative claim is absent."}
        for key in RUBRIC
    ]
    guard = {"status": "clear", "source": [], "response": "", "reason": "The fixed record uses the preserved source cards."}
    verdict = {"id": name, "units": units, "guard": guard}
    points = judge.score(packet, verdict)["final"]["lower"]
    assert points == sum(RUBRIC[key]["weight"] for key in visible)
    return packet, verdict, points


def run():
    results = read(HERE / "verified.json")["outputs"]
    reviewed = read(HERE / "marks.json")
    assert VIEWS.keys() == results.keys() == reviewed.keys()
    rows = {}
    for name, ids in VIEWS.items():
        packet, verdict, standalone = fixed_packet(name, ids)
        generated = results[name]
        sentence = native_sentence(name, generated)
        mark = reviewed[name]
        if sentence:
            packet["answer"] += "\n\n" + sentence
        verdict["units"] = [u if u["id"] != "joint-process" else mark["relation"] for u in verdict["units"]]
        verdict["guard"] = mark["guard"]
        assert mark["relation"]["status"] != "met" or set(ids) == POSITIVE
        grade = judge.score(packet, verdict)
        words = len(packet["answer"].split())
        assert words <= CASE["word_cap"]
        native = grade["final"]["lower"] if grade["guard"] == "clear" else 0
        role_gate = len({OWNERS[key] for key in ids}) == 2
        exact_pair = set(ids) == POSITIVE
        rows[name] = {
            "receipts": ids, "phrase": generated["text"], "candidate": sentence, "words": words,
            "record": packet["answer"], "raw": grade["final"]["lower"], "guard": grade["guard"],
            "standalone": standalone, "unrestricted": native,
            "two_delegation_gate": native if role_gate else standalone,
            "exact_pair_gate": native if exact_pair else standalone,
            "exact_pair_ceiling": standalone + (RUBRIC["joint-process"]["weight"] if exact_pair else 0),
            "input_tokens": generated["input_tokens"], "output_tokens": generated["output_tokens"],
        }
    partial = {name: fixed_packet(name, ids)[2]
               for name, ids in (("public", ()), ("de-process", ("de-process",)), ("de-fund", ("de-fund",)))}
    return {"views": rows, "fallback_partials": partial}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
