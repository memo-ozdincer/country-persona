"""Test one source-grounded clarification turn while holding chair inputs otherwise fixed."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_deliberation as prior
from facilitator_event_transfer import prompt

HERE = prior.HERE
base = prior.base
runner = prior.runner
ARCHIVE = HERE / "facilitator-deliberation-evidence/final-records.json"
FAMILY = "facilitator-clarification"
ARMS = ("independent", "asked", "no_reply")
# Assign the answering desk in advance, including the two positive controls.
TARGETS = {"bosnia-0": 1, "bosnia-1": 1, "afghanistan-0": 1, "afghanistan-1": 0}
QUESTION_CAP = 42
REPLY_CAP = 72
QUESTION = (
    "Ask the other delegate one evidence-checking question about the proposed joint statement. You see only your "
    "own documentary record. Ask whether their own official statement or recorded vote establishes their side, "
    "contradicts it, or leaves it open. Ask for the relevant limit or exact wording when it matters. "
    "Do not assert what the other delegation said. Output only the question."
)
ANSWER = (
    "Verify only this delegation's side of the proposed statement against the assigned source. If a peer question "
    "is supplied, address its relevant issue while preserving the scope of the target assertion. Distinguish "
    "sponsorship, consultations, initial draft circulation, adoption, and individual votes. Do not treat a "
    "different act as a contradiction. Return supports, contradicts, or unknown, a vertical bar, and an exact "
    "contiguous excerpt where available. For unknown you may cite a closely related passage or leave it blank. "
    "Do not insert a stance that the source does not document."
)
CHAIR = prior.CHAIR + (
    " Check that the heading matches what the final sentence establishes: both sides evidenced means retain, "
    "a documented contradiction means revise, and an unresolved side without contradiction means withhold. "
    "Only source cards can substantiate factual attributions. Verify the working answer against them."
)


def source_inputs():
    archived = base.load(ARCHIVE)[prior.FAMILY]
    for panel, proposal, local, expected, rubric, cards in prior.fixtures():
        openings = {f"S{i+1}": archived[f"{panel}/private/opening{i+1}"] for i in range(2)}
        target = TARGETS[panel]
        ask = 1 - target
        yield panel, proposal, local, expected, rubric, cards, openings, target, ask


def questions():
    for panel, proposal, _, _, _, cards, openings, target, ask in source_inputs():
        yield prompt(f"{panel}/question", QUESTION_CAP, QUESTION, {
            "asking_speaker": cards[ask][0], "your_card": cards[ask][1], "your_opening": openings[f"S{ask+1}"],
            "addressee": cards[target][0], "proposed_joint_statement": proposal,
        })


def answers(rows):
    for panel, _, local, _, _, cards, _, target, _ in source_inputs():
        speaker, source = cards[target]
        payload = {"speaker": speaker, "target_assertion": f"{speaker} {local}.", "source": source}
        for arm in ARMS[:2]:
            seen = {"peer_question": rows[f"{panel}/question"]["output"]} if arm == "asked" else {}
            yield prompt(f"{panel}/{arm}/answer", REPLY_CAP, ANSWER, payload | seen)


def finals(rows):
    for panel, proposal, _, _, _, cards, openings, target, _ in source_inputs():
        for arm in ARMS:
            payload = {"proposed_sentence": proposal,
                       "documentary_passages": {f"S{i+1}": c[1] for i, c in enumerate(cards)},
                       "working_notes": openings, "question": rows[f"{panel}/question"]["output"],
                       "answering_speaker": cards[target][0]}
            # The chair has no arm label. The same question enters all arms.
            answer = rows[f"{panel}/{arm}/answer"]["output"] if arm != "no_reply" else None
            yield prompt(f"{panel}/{arm}/final", base.CAP, CHAIR, payload | {"working_answer": answer})


def plan(generate):
    rows = {}
    for stage in (lambda _: questions(), answers, finals):
        rows.update(generate(list(stage(rows))))
    return [{"family": FAMILY, "final": rows}]


def pins():
    files = [Path(__file__), ARCHIVE, *(HERE.parents[1] / p for p in prior.pins())]
    return {str(p.resolve().relative_to(HERE.parents[1])): sha256(p.read_bytes()).hexdigest() for p in files}


def read(directory):
    from transformers import AutoTokenizer
    launch, finish = (base.load(directory / name) for name in ("launch.json", "complete.json"))
    raw, final = (directory / name for name in ("transcript.jsonl", "final-records.json"))
    assert launch["sha256"] == pins() and finish["transcript_sha256"] == runner.digest(raw)
    assert finish["final_records_sha256"] == runner.digest(final)
    token = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = token.convert_tokens_to_ids("<|im_end|>")
    rows = {r["id"]: r for r in map(json.loads, raw.read_text().splitlines())}
    prompts = [*questions(), *answers(rows), *finals(rows)]
    assert rows.keys() == {row["id"] for row in prompts} and len(rows) == finish["records"] == 24
    for expected in prompts:
        row = rows[expected["id"]]
        assert all(row[k] == v for k, v in expected.items()) and runner.encode(token, expected) == row["input_ids"]
        ids = row["output_ids"]
        assert 0 < len(ids) <= expected["cap"] and eos not in ids[:-1]
        assert row["ended"] == (ids[-1] == eos) and row["output"] == token.decode(ids, skip_special_tokens=True).strip()
    assert base.load(final) == {FAMILY: {k: v["output"] for k, v in rows.items()}}
    return rows


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("run", "verify"))
    p.add_argument("directory", type=Path)
    p.add_argument("--model", type=Path)
    args = p.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, episode=plan, locks=pins):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps({"verified_generations": len(read(args.directory))}))
