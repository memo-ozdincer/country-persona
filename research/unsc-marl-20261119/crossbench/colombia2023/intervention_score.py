"""Score the matched chair-only attribution perturbations."""
import json

from run import CASE, HERE, runner
from score import final_review

EVIDENCE = HERE / "intervention-evidence"


def run():
    rules = json.loads(CASE.read_text())["rules"]
    annotation = json.loads((HERE / "intervention-annotations.json").read_text())
    raw = EVIDENCE / "transcript.jsonl"
    assert annotation["transcript_sha256"] == runner.digest(raw)
    transcript = {row["id"]: row for row in map(json.loads, raw.read_text().splitlines())}
    assert transcript.keys() == annotation["records"].keys()
    scores = {}
    for arm, row in transcript.items():
        review = annotation["records"][arm]
        result = final_review(rules, row, review)
        a3 = review["a3_direction"]
        assert a3["span"] in row["output"]
        scores[arm] = {**result, "a3_direction": a3, "output_tokens": len(row["output_ids"]),
                       "input_tokens": len(row["input_ids"])}
    return {"scope": "Two chair-only follow-ups on the exposed Colombia docket. The frozen compact interactive "
                     "synthesis is the baseline. The earlier pooled analyst remains the budget-matched solo arm.",
            "controls": scores}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
