"""Render and quote-check the six model-conditioned 2553 final records."""
from copy import deepcopy
import json

from collect_transfer import ARCHIVE, HERE, RUNS, old, read
from fit import team

judge = old.typed.prior.load("reform_native_record_judge",
                            old.typed.prior.RELEASE / "judge_score.py")
CLAUSES = {
    "joint-process": "The UK and Germany shared concerns about compressed negotiations.",
    "joint-fund": "Belgium emphasized funding predictability and Germany clarified the Fund's governance.",
}


def render():
    results = read(HERE / "results.json")
    archive = read(ARCHIVE)["cases"]
    word_cap = read(RUNS / "reform-2553-transfer/docket.json")["word_cap"]
    rendered = {}
    for row in results["terminal_rows"]:
        if row["docket"] != "reform":
            continue
        key, chosen, expected = (row[name] for name in ("key", "predicted", "expected"))
        view, reply = key.split("/")
        datum = archive[view]["records"][reply]
        entry, marks = deepcopy(datum["packet"]), deepcopy(datum["verdict"])
        articles = [x["text"] for x in entry["evidence"]]
        if chosen:
            articles.append(CLAUSES[chosen])
        entry["answer"] = "\n\n".join(articles)
        assert len(entry["answer"].split()) <= word_cap
        for unit in marks["units"]:
            if unit["id"].startswith("joint-") and unit["id"] != chosen:
                unit.update(status="unmet", response="", source=[], reason="The final omits this relation.")
        if chosen and chosen == expected:
            item = next(x for x in marks["units"] if x["id"] == chosen)
            assert item["status"] == "met" and item["response"] == CLAUSES[chosen]
        if chosen and chosen != expected:
            marks["guard"] = {"status": "failed", "response": CLAUSES[chosen],
                              "source": [{"block": e["id"], "quote": e["text"]} for e in entry["evidence"][3:]],
                              "reason": "The selected relation is unsupported by this actual pair of receipts."}
        grade = judge.score(entry, marks)
        released = grade["final"]["lower"] if grade["guard"] == "clear" else 0
        assert released == row["audited"]
        rendered[key] = {"packet": entry, "marks": marks, "released_70": released}
    assert len(rendered) == len(team.PRIVATE["reform"]) * len(team.ACTIONS)
    return rendered


if __name__ == "__main__":
    print(json.dumps(render(), ensure_ascii=False, indent=2))
