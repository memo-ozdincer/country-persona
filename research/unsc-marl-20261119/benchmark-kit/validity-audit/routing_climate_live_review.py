"""Validate exact-span annotations and summarize a climate request intervention."""
import argparse
import json
from pathlib import Path

import routing_climate_live_exchange as live

read, digest = live.read, live.digest


def exact(text, quote):
    assert quote and quote in text, quote


def score(directory, annotations, verify=live.verify):
    trace = verify(directory)
    fixture = live.transfer.task()
    rubric = {row["id"]: row for row in fixture["private_criteria"]}
    source_text = {row["id"]: row["text"] for row in fixture["optional_sources"]}
    labels = read(annotations)
    first = trace["note-russia-explanation"]
    question = trace["question"]
    spoken = live.admit_question(question)
    assert spoken and labels["question"] in spoken and labels["scope"]
    assert set(labels["arms"]) == set(live.ARMS)
    scores = {}
    for arm in live.ARMS:
        review = labels["arms"][arm]
        reply = trace[f"reply-{arm}"]
        record = trace[f"chair-{arm}"]
        evidence = live.receipt(first, reply)
        assert set(evidence) == set(record["evidence_ids"])
        used_question = json.loads(reply["messages"][1]["content"])["incoming_question"]
        assert used_question == (spoken if arm == "received" else "")
        reply_id, admitted = live.admit_note(reply)
        initial_id, _ = live.admit_note(first, first["evidence_ids"][0])
        assert reply_id in evidence
        for idea in review["reply_ideas"]:
            exact(admitted, idea["reply_span"])
            exact(source_text[reply_id], idea["source_span"])
            assert idea["description"]
            assert isinstance(idea["new_to_chair"], bool)
        assert len({idea["description"] for idea in review["reply_ideas"]}) == len(review["reply_ideas"])

        for key, criterion in review["met"].items():
            required = set(rubric[key]["required_fields"])
            assert required <= evidence.keys()
            assert set(criterion["evidence"]) == required
            exact(record["output"], criterion["record"])
            for field, quote in criterion["evidence"].items():
                exact(evidence[field], quote)
        for quote in review["issues"].values():
            exact(record["output"], quote)

        assert review["guard"] in {"clear", "failed", "uncertain"} and review["reason"]
        words = len(record["output"].split())
        public_points = 7 * len(fixture["public_criteria"])
        raw_points = public_points + sum(rubric[key]["points"] for key in review["met"])
        eligible = record["ended"] and words <= 75 and review["guard"] == "clear"
        scores[arm] = {
            "reply_field": reply_id,
            "new_annex_from_reply": reply_id != initial_id,
            "grounded_reply_ideas": len(review["reply_ideas"]),
            "new_grounded_reply_ideas": sum(idea["new_to_chair"] for idea in review["reply_ideas"]),
            "chair_annexes": list(evidence),
            "raw_points_out_of_70": raw_points,
            "eligible_points_out_of_70": raw_points if eligible else 0,
            "supplement_words": words,
            "guard": review["guard"],
            "peer_exchange_turns_delivered": 2 if used_question else 1,
            "question_and_reply_words_delivered": len(used_question.split()) + len(admitted.split()),
            "input_tokens": sum(len(row["input_ids"]) for row in (first, question, reply, record)),
            "generated_tokens": sum(len(row["output_ids"]) for row in (first, question, reply, record)),
            "generated_token_ceiling": sum(row["cap"] for row in (first, question, reply, record)),
        }
    return {"scope": labels["scope"], "trace_sha256": digest(directory / "transcript.jsonl"),
            "annotations_sha256": digest(annotations), "scores": scores}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    cli.add_argument("annotations", type=Path)
    writer = cli.add_mutually_exclusive_group()
    writer.add_argument("--attribution", action="store_true")
    writer.add_argument("--isolated", action="store_true")
    writer.add_argument("--coverage", action="store_true")
    args = cli.parse_args()
    verifier = live.verify
    if args.attribution:
        import routing_climate_live_attribution as attribution

        verifier = attribution.verify
    if args.isolated:
        import routing_climate_live_isolated as isolated

        verifier = isolated.verify
    if args.coverage:
        import routing_climate_live_coverage as coverage

        verifier = coverage.verify
    print(json.dumps(score(args.directory, args.annotations, verifier), indent=2, ensure_ascii=False))
