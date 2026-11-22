"""Run a frozen writer once for every distinct nonempty source receipt."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "validity-audit"))
import source_record_run as runner

MODEL = Path("/mfs1/u/memo/country-persona-research/models/Qwen3.5-4B/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a")
PACKET = HERE / "packet.json"
EVIDENCE = HERE / "writer-evidence"
FAMILY = "tribunals2422-transfer"


def read(path):
    return json.loads(path.read_text())


def requests():
    packet = read(PACKET)
    instruction = (
        "Write only an attributed supplement to a historical Security Council record. At most 70 words. "
        "Use the evidence supplied here and keep each position with its speaker. Preserve concrete reasons "
        "and conditions, including who made each request or decision. Attribute complaints as complaints. "
        "A verified Council decision and vote appear separately. Output the supplement alone."
    )
    for receipt in range(1, 8):
        evidence = [{"speaker": card["desk"], "statements": [a["text"] for a in card["atoms"]]}
                    for i, card in enumerate(packet["cards"]) if receipt & (1 << i)]
        yield {"id": str(receipt), "cap": 150, "messages": [
            {"role": "system", "content": instruction},
            {"role": "user", "content": json.dumps(evidence, ensure_ascii=False)},
        ]}


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(requests()))}]


def locks():
    files = (Path(__file__), PACKET, HERE / "protocol.md", HERE / "writer-protocol.md",
             HERE / "forecast.json", Path(runner.__file__))
    return {p.name: runner.digest(p) for p in files}


def verify():
    from transformers import AutoTokenizer

    complete = read(EVIDENCE / "complete.json")
    launch = read(EVIDENCE / "launch.json")
    trace = EVIDENCE / "transcript.jsonl"
    final = EVIDENCE / "final-records.json"
    assert launch["sha256"] == locks()
    assert complete["transcript_sha256"] == runner.digest(trace)
    assert complete["final_records_sha256"] == runner.digest(final)
    tokenizer = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    rows = [json.loads(line) for line in trace.read_text().splitlines()]
    assert complete["records"] == len(rows) == 7
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    for request, row in zip(requests(), rows, strict=True):
        assert all(row[k] == value for k, value in request.items())
        assert runner.encode(tokenizer, request) == row["input_ids"]
        assert 0 < len(row["output_ids"]) <= request["cap"]
        assert tokenizer.decode(row["output_ids"], skip_special_tokens=True).strip() == row["output"]
        assert eos not in row["output_ids"][:-1] and row["ended"] == (eos == row["output_ids"][-1])
    assert read(final)[FAMILY] == {row["id"]: row["output"] for row in rows}
    return {"verified_calls": len(rows), "finished": sum(r["ended"] for r in rows)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "verify"))
    args = parser.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, episode=episode, locks=locks):
            runner.run(MODEL, EVIDENCE)
    else:
        print(json.dumps(verify(), indent=2))
