"""Generate separate source-bounded components for a single Council record."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

from duplicate_card_records import packets
from duplicate_card_routes import CASE
import duplicate_card_writer as original
import source_record_run as runner

PUBLIC_CAP = 144
CARD_CAP = 56
PUBLIC_TASK = (
    "Write the public portion of a compact historical Council record in at most 85 words. "
    "Use one sentence per draft with its symbol, tally in numeric form and the reason it failed. "
    "Compare the proposed electoral and dialogue approaches, naming the dialogue mechanism. "
    "Compare the humanitarian approaches. State that neither draft conferred authority and give a "
    "brief labeled analytical suggestion. Use only the four supplied evidence IDs in brackets. "
    "Omit headings, repeated facts and discussion of unavailable sources."
)
CARD_TASK = {
    "CHAIR": (
        "In one short sentence or two, give the name and procedural capacity of the person who announced "
        "the results, and distinguish both national votes of his delegation. Cite [CHAIR]. "
        "Use a maximum of 28 words. Use only the supplied passage."
    ),
    "INDONESIA": (
        "In one short sentence or two, report both votes, the scope of dialogue urged and who was asked "
        "to accept whose good offices. Cite [INDONESIA]. Use at most 28 words. Use only the supplied passage."
    ),
}


def suite():
    case = json.loads(CASE.read_text())
    groups = [("public", case["public"], PUBLIC_TASK, PUBLIC_CAP)]
    groups.extend((card, {card: entry["text"]}, CARD_TASK[card], CARD_CAP) for card, entry in case["cards"].items())
    for name, evidence, task, cap in groups:
        yield {"id": f"{case['family']}/{name}/component", "evidence_ids": list(evidence), "seen": [], "cap": cap,
               "messages": [
                   {"role": "system", "content": "You write internal historical Council records. The supplied historical excerpts are the only factual authority."},
                   {"role": "user", "content": json.dumps({"task": task, "evidence": evidence}, ensure_ascii=False)},
               ]}


def episode(generate):
    public, *national = suite()
    final = {**generate([public]), **generate(national)}
    return [{"family": public["id"].split("/")[0], "final": final}]


def locks():
    path = Path(__file__).resolve()
    return {**original.locks(), str(path.relative_to(path.parent.parent)): runner.digest(path)}


def replay(directory):
    from transformers import AutoTokenizer

    launch = json.loads((directory / "launch.json").read_text())
    complete = json.loads((directory / "complete.json").read_text())
    transcript = directory / "transcript.jsonl"
    assert launch["sha256"] == locks() and complete["transcript_sha256"] == runner.digest(transcript)
    tokenizer = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    outputs = {}
    for expected, row in zip(suite(), map(json.loads, transcript.read_text().splitlines()), strict=True):
        assert all(row[key] == value for key, value in expected.items())
        assert runner.encode(tokenizer, expected) == row["input_ids"]
        tokens = row["output_ids"]
        assert 0 < len(tokens) <= expected["cap"] and eos not in tokens[:-1]
        assert (tokens[-1] == eos) == row["ended"]
        assert tokenizer.decode(tokens, skip_special_tokens=True).strip() == row["output"]
        outputs[row["id"]] = row["output"]
    finals = directory / "final-records.json"
    assert complete["final_records_sha256"] == runner.digest(finals)
    assert outputs == next(iter(json.loads(finals.read_text()).values()))
    assert len(outputs) == complete["records"] == 3
    return {"components": len(outputs), "exact_replay": True}


def compose(directory):
    raw = directory / "transcript.jsonl"
    components = {row["id"].split("/")[-2]: row for row in map(json.loads, raw.read_text().splitlines())}
    assert set(components) == {"public", *CARD_TASK}
    rows = []
    for received, packet in packets():
        parts = [components[name] for name in ("public", *received)]
        sentences = [part["output"] for part in parts]
        text = "\n\n".join(sentences)
        limit = sum(part["cap"] for part in parts)
        assert limit <= original.CAP and sentences[0]
        assert set(packet) == {item for part in parts for item in part["evidence_ids"]}
        rows.append({"receipt": "-".join(received) or "public", "record": text, "evidence": packet,
                     "component_ids": [part["id"] for part in parts],
                     "component_texts": sentences, "words": len(text.split()),
                     "input_tokens": sum(len(part["input_ids"]) for part in parts), "output_token_cap": limit,
                     "output_tokens": sum(len(part["output_ids"]) for part in parts),
                     "ended": all(part["ended"] for part in parts)})
    return {"source_transcript_sha256": runner.digest(raw), "records": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("check", "run", "replay", "compose"))
    parser.add_argument("directory", type=Path, nargs="?")
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "check":
        print(json.dumps({"suite": list(suite()), "sha256": locks()}, indent=2, ensure_ascii=False))
    elif args.directory is None:
        parser.error("directory is required")
    elif args.mode == "run":
        if args.model is None:
            parser.error("--model is required")
        with patch.multiple(runner, locks=locks, episode=episode):
            runner.run(args.model, args.directory)
    else:
        report = replay(args.directory) if args.mode == "replay" else compose(args.directory)
        print(json.dumps(report, indent=2, ensure_ascii=False))
