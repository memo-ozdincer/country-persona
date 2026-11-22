"""Test text interaction under matched peer-visible, independent and pooled conditions."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_witness_writer as writer
import facilitator_event_transfer as previous

HERE = writer.HERE
runner = writer.runner
base = writer.base
PACK = HERE / "facilitator-deliberation-panels.json"
FAMILY = "facilitator-deliberation"
ARMS = ("independent", "peer", "solo")
REVISION = (
    writer.TASK + " Revise your draft. If a peer draft is present, consider whether it identifies a difference in "
    "scope, authority, or position. Ground the new sentence in the assigned speaker's source and attribute only "
    "that speaker's position. A peer draft may be wrong."
)
CHAIR = base.TASK + " Use working drafts as suggestions. Verify factual statements against the source cards."


def fixtures():
    for docket, case in base.load(PACK).items():
        for index, (proposal, local, expected, rubric) in enumerate(case["proposals"]):
            yield f"{docket}-{index}", proposal, local, expected, rubric, case["sources"]


def role_payload(cards, slot, local, pooled=False):
    speaker, source = cards[slot]
    payload = {"speaker": speaker, "one_speaker_assertion": f"{speaker} {local}.", "source": source}
    if pooled:
        other, passage = cards[1-slot]
        payload["other_documentary_card"] = {"speaker": other, "source": passage}
    return payload


def openings():
    for panel, _, local, _, _, cards in fixtures():
        for team in ("private", "solo"):
            for i in range(2):
                yield previous.prompt(f"{panel}/{team}/opening{i+1}", writer.CAP, writer.TASK,
                                      role_payload(cards, i, local, team == "solo"))


def revisions(rows):
    for panel, _, local, _, _, cards in fixtures():
        for arm in ARMS:
            pool = arm == "solo"
            precursor = "solo" if pool else "private"
            for i in range(2):
                payload = role_payload(cards, i, local, pool)
                payload["own_draft"] = rows[f"{panel}/{precursor}/opening{i+1}"]["output"]
                if arm == "peer":
                    payload["peer_draft"] = rows[f"{panel}/private/opening{2-i}"]["output"]
                elif pool:
                    payload["other_working_note"] = rows[f"{panel}/solo/opening{2-i}"]["output"]
                yield previous.prompt(f"{panel}/{arm}/revision{i+1}", writer.CAP, REVISION, payload)


def finals(rows):
    for panel, proposal, _, _, _, cards in fixtures():
        for arm in ARMS:
            notes = {f"S{i+1}": rows[f"{panel}/{arm}/revision{i+1}"]["output"] for i in range(2)}
            payload = {"proposed_sentence": proposal, "documentary_passages": {f"S{i+1}": c[1] for i, c in enumerate(cards)},
                       "working_notes": notes}
            yield previous.prompt(f"{panel}/{arm}/final", base.CAP, CHAIR, payload)


def plan(generate):
    rows = {}
    for stage in (lambda _: openings(), revisions, finals):
        batch = list(stage(rows))
        for i in range(0, len(batch), 12):
            rows.update(generate(batch[i:i+12]))
    return [{"family": FAMILY, "final": rows}]


def pins():
    files = [Path(__file__), PACK, *(HERE.parents[1] / p for p in writer.pins())]
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
    plan = [*openings(), *revisions(rows), *finals(rows)]
    assert rows.keys() == {r["id"] for r in plan} and len(rows) == finish["records"] == len(plan) == 52
    for expected in plan:
        row = rows[expected["id"]]
        assert all(row[k] == v for k, v in expected.items()) and runner.encode(token, expected) == row["input_ids"]
        ids = row["output_ids"]
        assert 0 < len(ids) <= expected["cap"] and eos not in ids[:-1]
        assert row["ended"] == (ids[-1] == eos) and row["output"] == token.decode(ids, skip_special_tokens=True).strip()
    assert base.load(final) == {FAMILY: {key: row["output"] for key, row in rows.items()}}
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
