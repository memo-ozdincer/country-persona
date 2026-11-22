"""Project validated comparisons into a common record and replay policy values."""
import json

from collect_anchored import HERE, PREVIOUS, plan, prior

earlier = prior.load("native_team_policy_replay", PREVIOUS / "score.py")
fixture = prior.fixture
read = prior.read


def comparison(mode, row):
    reply = row["reply"]
    text = reply["text"].strip()
    if reply["termination"] != "complete":
        return "", "termination_" + reply["termination"], []
    if text == "NONE":
        return "", "abstained", []
    anchors = []
    if mode == "witness":
        lines = text.splitlines()
        prefixes = ("EARLY: ", "LATE: ", "LINK: ")
        if len(lines) != 3 or not all(x.startswith(p) for x, p in zip(lines, prefixes, strict=True)):
            return "", "witness_format", []
        *anchors, text = [x[len(p):].strip() for x, p in zip(lines, prefixes, strict=True)]
        if not all(x and x in fixture.BLOCKS[key]["text"]
                   for x, key in zip(anchors, row["receipts"], strict=True)):
            return "", "witness_span", anchors
    if not 0 < len(text.split()) <= 42:
        return "", "comparison_length", anchors
    source_length = sum(len(x["text"].split()) for x in prior.blocks(*row["receipts"]))
    if source_length + len(text.split()) > fixture.CASE["word_cap"]:
        return "", "final_word_cap", anchors
    return text, None, anchors


def document(receipts, text="", status="clear"):
    cards = prior.blocks(*receipts)
    score = sum(c["weight"] for c in cards)
    record = "\n\n".join([*(b["text"] for b in cards), *([text] if text else [])])
    relation = next((r for r in fixture.RELATIONS if set(r["requires"]) <= set(receipts)), None)
    if status == "met":
        assert relation and text
    bonus = relation["weight"] if status == "met" else 0
    return {"record": record, "fallback_standalone": score, "raw_70": score + bonus,
            "released_70": 0 if status in {"failed", "uncertain"} else score + bonus,
            "released_relationship": bonus, "relationship": relation["id"] if relation else None}


def run():
    assert plan() == read(HERE / "plan.json")
    outputs = read(HERE / "verified.json")["outputs"]
    marks = read(HERE / "marks.json")
    assert outputs.keys() == marks.keys()
    base = {key: document(row["receipts"]) for key, row in fixture.cases()[0].items()}
    banks = {"standalone": base, "direct": base.copy(), "witness": base.copy()}
    grades = {}
    for key, row in outputs.items():
        mode, left, right = key.split("/")
        suffix = f"{left}/{right}"
        text, fallback, witnesses = comparison(mode, row)
        mark = marks[key]
        assert set(mark) == {"comparison", "status", "reason", "source"} and mark["comparison"] == text
        status = mark["status"]
        assert status in {"met", "clear", "failed", "uncertain", "dropped"}
        assert bool(text) == (status != "dropped")
        assert mark["reason"].strip()
        source = earlier.judge.by_id(prior.blocks(*row["receipts"]))
        earlier.judge.citations(mark["source"], source)
        if status in {"met", "failed", "uncertain"}:
            assert {e["block"] for e in mark["source"]} == set(row["receipts"])
        bank = document(row["receipts"], text, status)
        grades[key] = bank | {"fallback_reason": fallback, "witnesses": witnesses, "status": status}
        banks[mode][suffix] = bank
    team = read(prior.TEAM / "results.json")
    previous = read(PREVIOUS / "results.json")
    results = {key: earlier.evaluate(bank, team) for key, bank in banks.items()}
    return {"grades": grades, "policies": results, "previous_full": previous["live"]["summary"],
            "archival": previous["authored"]["summary"]}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
