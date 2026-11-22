"""Grade the recorded provenance interventions with the original case rubric."""
import json

from run import CASE, HERE, runner
from score import final_review

EVIDENCE = HERE / "provenance-evidence"


def run():
    rules = json.loads(CASE.read_text())["rules"]
    reviewed = json.loads((HERE / "provenance-annotations.json").read_text())
    raw = EVIDENCE / "transcript.jsonl"
    assert reviewed["transcript_sha256"] == runner.digest(raw)
    rows = {row["id"]: row for row in map(json.loads, raw.read_text().splitlines())}
    assert rows.keys() == reviewed["records"].keys()
    results = {}
    compact = {r["id"].split("/", 1)[-1]: r for r in
               map(json.loads, (HERE / "compact-evidence/transcript.jsonl").read_text().splitlines())}
    for name, row in rows.items():
        review = reviewed["records"][name]
        body = json.loads(row["messages"][1]["content"])
        for relation in (review["a3"], review["brazil"]):
            assert relation["span"] in row["output"]
        revision = "independent_drafts/revision_0" if name == "ledger_both_reversed" else "interactive/revision_0"
        assert compact[revision]["output"] == body["working_notes"][0]
        a3_original = compact["interactive/revision_1"]["output"]
        a3_modified = body["working_notes"][1] != a3_original
        results[name] = {**final_review(rules, row, review), "a3": review["a3"], "brazil": review["brazil"],
                         "output_tokens": len(row["output_ids"]), "input_tokens": len(row["input_ids"]),
                         "actual_brazil_note_turn": compact[revision]["id"],
                         "a3_note_is_perturbed": a3_modified}
    return {"scope": "Frozen-chair source-check intervention with same-assistant structured source fields and review. "
                     "The seen metadata describes the parent plan slots. Actual note text and donor are checked here.",
            "records": results}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
