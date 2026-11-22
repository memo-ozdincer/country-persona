"""Score the unchanged clause-writing prompt on matched UNAMI views."""
import json

import payload_writer_contract_transfer as transfer
from private_deliberation_score import RUBRIC
from private_payload_score import checked

REVIEW = transfer.HERE / "payload-writer-transfer-review.json"
REVIEW_FACTS = {"review_kind", "review_actor", "review_recipient", "review_deadline"}
LICENSES = {"full": set(RUBRIC["unami"]), "recurring_and_review": REVIEW_FACTS | {"periodic_report"},
            "review_only": REVIEW_FACTS}


def run():
    raw = transfer.replay(transfer.ROOT)
    review = json.loads(REVIEW.read_text())
    assert review["transcript_sha256"] == transfer.runner.digest(transfer.ROOT / "transcript.jsonl")
    assert review["records"].keys() == raw.keys()
    result = {}
    for view in transfer.VIEWS:
        choices = {}
        for variant in ("original", "separate"):
            identifier = f"{variant}/{view}"
            row = raw[identifier]
            reviewed = review["records"][identifier]
            facts = checked(reviewed, row["output"], RUBRIC["unami"])
            words = len(row["output"].split())
            evidence = json.loads(row["messages"][1]["content"])
            assert len(evidence["working_notes"]) == len(row["seen"])
            for fact in LICENSES[view]:
                source = RUBRIC["unami"][fact][1]
                assert any(source in note for note in evidence["working_notes"])
            choices[variant] = {
                "supported_facts": sorted(facts & LICENSES[view]),
                "supported_count": len(facts & LICENSES[view]),
                "unavailable_facts": sorted(facts - LICENSES[view]),
                "points_available": len(LICENSES[view]),
                "finished": row["ended"], "words": words,
                "outputs_within_73_words": words <= 73,
                "input_tokens": len(row["input_ids"]), "output_tokens": len(row["output_ids"]),
                "conflicts": reviewed["conflicts"],
                "exact_support_and_clean": facts == LICENSES[view] and not reviewed["conflicts"]
                                           and row["ended"] and words <= 73,
                "wanted_paragraphs": len(row["seen"]),
                "actual_paragraphs": len(row["output"].split("\n\n")),
            }
        result[view] = choices
    return {"scope": "Matched Qwen calls on three UNAMI source views and exact-span same-assistant review. "
                     "The separate-clause prompt is transferred unchanged. The observed cases share one docket.",
            "cases": result, "annotations": review["records"]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
