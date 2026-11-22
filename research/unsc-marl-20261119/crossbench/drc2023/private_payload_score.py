"""Audit which facts crossed a matched 48-token source channel."""
import json

import private_payload as trial
from private_deliberation_score import RUBRIC

HERE = trial.HERE
EVIDENCE = HERE / "private-payload-evidence"


def checked(annotation, text, rubric):
    facts = annotation["facts"]
    assert facts.keys() <= rubric.keys()
    assert all(spans and all(span in text for span in spans) for spans in facts.values())
    assert all(span in text for span in annotation["conflicts"])
    return set(facts)


def run():
    rows, tokenizer = trial.replay(EVIDENCE)
    review = trial.parent.read(HERE / "private-payload-review.json")
    assert review["transcript_sha256"] == trial.runner.digest(EVIDENCE / "transcript.jsonl")
    cases = {}
    consumed = set()
    for family, _, _ in trial.parent.fixtures():
        rubric = RUBRIC[family]
        arms = {}
        for arm in trial.ARMS:
            key = f"{family}/{arm}"
            row = rows[key]
            a, b = row["seen"]
            chair = json.loads(row["messages"][1]["content"])
            left, right = chair["working_notes"]
            assert not chair["local_source_cards"]
            informed = arm == "interactive"
            generated = arm in {"interactive", "independent"}
            calls = [rows[a], rows[b], row] if generated else [row]
            consumed.update((a, b, key))
            a_review, b_review, final_review = (review["records"][name] for name in (a, b, key))
            first = checked(a_review, left, rubric)
            second = checked(b_review, right, rubric)
            final = checked(final_review, row["output"], rubric)
            declared_a = {fact for fact, (desk, _) in rubric.items() if desk == "A"}
            declared_b = set(rubric) - declared_a
            supplied_a = first & declared_a
            supplied_b = second & (declared_b | (supplied_a if informed else set()))
            delivered = supplied_a | supplied_b
            retained = final & delivered
            first_tokens, second_tokens = (len(trial.payload_tokens(tokenizer, text)) for text in (left, right))
            assert first_tokens <= trial.LIMIT and second_tokens <= trial.LIMIT
            if generated:
                payload = json.loads(rows[b]["messages"][1]["content"])["working_notes"]
                assert payload == ([left] if informed else [])
            words = len(row["output"].split())
            arms[arm] = {
                "chair_payload_tokens": [first_tokens, second_tokens],
                "peer_payload_tokens": first_tokens if informed else 0,
                "total_transmitted_payload_tokens": first_tokens + second_tokens + (first_tokens if informed else 0),
                "transmitted_facts": sorted(delivered),
                "unique_facts_a": sorted(supplied_a - supplied_b),
                "unique_facts_b": sorted(supplied_b - supplied_a),
                "echoed_facts": sorted(supplied_a & supplied_b),
                "sender_conflicts": a_review["conflicts"] + b_review["conflicts"],
                "supported_final_facts": sorted(retained), "count_of_8": len(retained),
                "correct_but_unwitnessed": sorted(final - retained),
                "final_conflicts": final_review["conflicts"], "final_finished": row["ended"],
                "final_words": words,
                "strict": len(retained) == len(rubric) and not final_review["conflicts"] and row["ended"] and words <= 73,
                "generation_finished_by_call": {r["id"]: r["ended"] for r in calls},
                "generated_output_tokens": sum(len(r["output_ids"]) for r in calls),
                "total_model_input_tokens": sum(len(r["input_ids"]) for r in calls),
            }
        cases[family] = arms
    assert consumed == review["records"].keys()
    return {"scope": "Same-assistant same-rubric review. Only facts supported by the actual transmitted text "
                     "receive final credit. The payload count excludes JSON and protocol envelopes. "
                     "The interactive arm pays an additional A-to-B hop.",
            "maximum_chair_payload_per_desk": trial.LIMIT, "dockets": cases, "annotations": review["records"]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
