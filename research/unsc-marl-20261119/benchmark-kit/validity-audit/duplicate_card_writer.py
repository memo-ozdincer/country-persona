"""Run one frozen chair on the four evidence packets induced by the routes."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

from duplicate_card_records import FIT, packets
from duplicate_card_routes import CASE
import source_record_run as runner

HERE = Path(__file__).resolve().parent
CAP = 256


def suite():
    case = json.loads(CASE.read_text())
    instructions = (
        case["task"] + " Use at most 120 words and put both complete vote tallies first. Use compact sentences "
        "without an introduction, repeated vote section or conclusion. State distinct proposals and the humanitarian "
        "comparison. Include national positions only when the corresponding source is present. End with one short "
        "hypothetical analytical next step that does not purport to create Council authority."
    )
    for received, packet in packets():
        yield {"id": f"{case['family']}/{'-'.join(received) or 'public'}/chair",
               "evidence_ids": list(packet), "seen": [], "cap": CAP,
               "messages": [
                   {"role": "system", "content": "You write internal historical Council records. The supplied historical excerpts are the only factual authority."},
                   {"role": "user", "content": json.dumps({"task": instructions, "evidence": packet}, ensure_ascii=False)},
               ]}


def episode(generate):
    batch = list(suite())
    return [{"family": batch[0]["id"].split("/")[0], "final": generate(batch)}]


def locks():
    paths = (CASE, FIT, Path(__file__), HERE / "source_record_run.py", HERE / "duplicate_card_records.py",
             HERE / "duplicate_card_routes.py")
    return {str(p.relative_to(HERE.parent)): runner.digest(p) for p in paths}


def replay(directory):
    from transformers import AutoTokenizer

    launch = json.loads((directory / "launch.json").read_text())
    complete = json.loads((directory / "complete.json").read_text())
    raw = directory / "transcript.jsonl"
    assert launch["sha256"] == locks()
    assert complete["transcript_sha256"] == runner.digest(raw)
    tokenizer = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    restored = {}
    for expected, row in zip(suite(), map(json.loads, raw.read_text().splitlines()), strict=True):
        assert all(row[key] == value for key, value in expected.items())
        assert row["input_ids"] == runner.encode(tokenizer, expected)
        output = row["output_ids"]
        assert 0 < len(output) <= expected["cap"] and eos not in output[:-1]
        assert (output[-1] == eos) == row["ended"]
        assert tokenizer.decode(output, skip_special_tokens=True).strip() == row["output"]
        restored[row["id"]] = row["output"]
    finals = directory / "final-records.json"
    assert complete["final_records_sha256"] == runner.digest(finals)
    assert restored == next(iter(json.loads(finals.read_text()).values()))
    assert len(restored) == complete["records"] == 4
    return {"records": len(restored), "exact_replay": True}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "replay", "check"))
    cli.add_argument("directory", type=Path, nargs="?")
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "check":
        print(json.dumps({"suite": list(suite()), "sha256": locks()}, indent=2, ensure_ascii=False))
    elif args.mode == "run":
        if args.directory is None or args.model is None:
            cli.error("inference requires directory and --model")
        with patch.multiple(runner, locks=locks, episode=episode):
            runner.run(args.model, args.directory)
    else:
        if args.directory is None:
            cli.error("replay requires directory")
        print(json.dumps(replay(args.directory), indent=2))
