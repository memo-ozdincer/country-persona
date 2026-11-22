"""Score the length and subject-separation comparison."""
import json

from run import CASE, HERE, runner
from score import final_review

DIRECTORY = HERE / "structured-evidence"


def run():
    raw = DIRECTORY / "transcript.jsonl"
    observations = {row["id"]: row for row in map(json.loads, raw.read_text().splitlines())}
    contract = json.loads(CASE.read_text())
    review = json.loads((HERE / "structured-annotations.json").read_text())
    assert review["transcript_sha256"] == runner.digest(raw)
    assert observations.keys() == review["records"].keys()
    output = {}
    for name, row in observations.items():
        annotation = review["records"][name]
        score = final_review(contract["rules"], row, annotation)
        for key in ("a3", "brazil", "shared_ground"):
            assert annotation[key]["span"] in row["output"]
        output[name] = {**score, "a3": annotation["a3"], "brazil": annotation["brazil"],
                        "shared_ground": annotation["shared_ground"], "within_145_words": score["word_count"] <= 145,
                        "output_tokens": len(row["output_ids"]),
                        "paragraphs": len(row["output"].split("\n\n"))}
    return {"scope": "Same-assistant exact-span scoring. The two chairs see both erroneous notes and the same documentary fields.",
            "conditions": output}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
