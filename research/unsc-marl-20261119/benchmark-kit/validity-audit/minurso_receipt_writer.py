"""Measure actual complete records on the four Western Sahara evidence receipts."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import source_record_run as runner
from source_record_minurso import PACK

FAMILY = "western-sahara-receipts"
CAP = 270
JUDGE = PACK.parents[2] / "judge/minurso-atomic-rubric.json"
SYSTEM = (
    "Write the final historical record using only the evidence actually delivered below. Output the five requested lines, "
    "one per heading, and stop. Retain exact vote tallies, instrument identifiers and qualifiers. Absent evidence means "
    "omit the claim or say its source was not received. Do not infer a national vote, speaker capacity or explanation from "
    "another country's evidence or from the Council tally. No preamble or afterword. Keep the record at most 155 words."
)
HEADINGS = {
    "Adoption": "Main draft and final resolution, tally and Algeria's participation status.",
    "Amendments": "Each amendment's identifier, distinct proposal, outcome and tally. Keep considering a change separate from making it.",
    "Algeria": "The stated reason involving the penholder and the national position on monitoring, if the national statement arrived.",
    "Switzerland": "Both national amendment votes and the stated reason for the second, if the national statement arrived.",
    "Authority": "Mandate end date, OHCHR access language and whether the adopted text added monitoring functions.",
}


def case():
    source, = json.loads(PACK.read_text())["cases"]
    return source


def requests():
    source = case()
    assert tuple(source["delegate_evidence"]) == ("Algeria", "Switzerland")
    for mask in range(4):
        evidence = dict(source["docket"])
        for seat, cards in enumerate(source["delegate_evidence"].values()):
            if mask & (1 << seat):
                evidence.update(cards)
        payload = {"headings": HEADINGS, "delivered_evidence": evidence,
                   "citation_rule": "Cite the source IDs in square brackets on each line that contains claims."}
        yield {"id": f"receipt-{mask}", "evidence_ids": list(evidence), "seen": [], "cap": CAP,
               "messages": [{"role": "system", "content": SYSTEM},
                            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]}


def locks():
    files = (Path(__file__), Path(runner.__file__), PACK, JUDGE)
    return {path.name: runner.digest(path) for path in files}


def run(model, directory):
    def episode(generate):
        return [{"family": FAMILY, "final": generate(list(requests()))}]

    with patch.object(runner, "episode", episode), patch.object(runner, "locks", locks):
        runner.run(model, directory)


def replay(directory):
    from transformers import AutoTokenizer

    start = json.loads((directory / "launch.json").read_text())
    end = json.loads((directory / "complete.json").read_text())
    trace = directory / "transcript.jsonl"
    assert start["sha256"] == locks() and end["transcript_sha256"] == runner.digest(trace)
    rows = list(map(json.loads, trace.read_text().splitlines()))
    assert len(rows) == end["records"] == 4
    tokenizer = AutoTokenizer.from_pretrained(start["model"], local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    for actual, expected in zip(rows, requests(), strict=True):
        assert all(actual[k] == v for k, v in expected.items())
        assert runner.encode(tokenizer, expected) == actual["input_ids"]
        out = actual["output_ids"]
        assert 0 < len(out) <= CAP and eos not in out[:-1]
        assert tokenizer.decode(out, skip_special_tokens=True).strip() == actual["output"]
        assert (out[-1] == eos) == actual["ended"]
    finals = directory / "final-records.json"
    assert runner.digest(finals) == end["final_records_sha256"]
    assert json.loads(finals.read_text()) == {FAMILY: {row["id"]: row["output"] for row in rows}}
    return rows


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "replay"))
    cli.add_argument("directory", type=Path, nargs="?")
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "check":
        prompts = list(requests())
        assert [len(x["evidence_ids"]) for x in prompts] == [3, 5, 5, 7]
        print(json.dumps({"evidence_ids": [x["evidence_ids"] for x in prompts], "hashes": locks()}, indent=2))
    elif args.mode == "run":
        if args.model is None or args.directory is None:
            cli.error("run requires directory and model")
        run(args.model, args.directory)
    else:
        print(json.dumps(replay(args.directory), ensure_ascii=False, indent=2))
