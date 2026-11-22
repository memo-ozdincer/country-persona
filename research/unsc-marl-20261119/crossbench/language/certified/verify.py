"""Replay certified inputs and tokens, then produce an opaque semantic review deck."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

from transformers import AutoTokenizer

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("certificate_runner", HERE / "run.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

from verify import mechanical
from run import ROOT, FAMILY, inputs
from packets import packet

sys.path.insert(0, str(ROOT.parent / "judge"))
from score import request


def audit(base, out):
    launch = json.loads((base / "launch.json").read_text())
    done = json.loads((base / "complete.json").read_text())
    lock = json.loads((HERE / "runner-lock.json").read_text())
    assert runner.digest(base / "launch.json") == lock["launch_sha256"]
    assert launch["pid"] == lock["pid_checked_live"]
    assert runner.digest(HERE / "run.py") == lock["certified_run_sha256"]
    for path in (HERE.parent / "run.py", HERE.parent / "available.py", runner.SOURCE / "availability-annotations.json"):
        assert runner.digest(path) == launch["input_sha256"][path.name]
    for name in ("transcript.jsonl", "complete.json"):
        assert runner.digest(runner.SOURCE / name) == launch["input_sha256"][name]
    assert runner.digest(base / "transcript.jsonl") == done["transcript_sha256"]
    assert launch["optimizer_updates"] == done["optimizer_updates"] == 0
    suite, previous = runner.inputs()
    records = [json.loads(line) for line in (base / "transcript.jsonl").read_text().splitlines()]
    assert done["records"] == len(records) == len(suite) == 4
    tokenizer = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    cases, _ = inputs()
    family = next(r for r in cases["families"] if r["id"] == FAMILY)
    deck, key, marks = [], {}, {}
    for row, req in zip(records, suite, strict=True):
        assert all(row[k] == v for k, v in req.items())
        older = previous[row["id"]]
        assert older["cap"] == row["cap"] == 240
        augmented = json.loads(row["messages"][1]["content"])
        added = augmented.pop("compatibility_check")
        assert augmented == json.loads(older["messages"][1]["content"])
        assert row["messages"][0] == older["messages"][0]
        text = tokenizer.apply_chat_template(row["messages"], tokenize=False, add_generation_prompt=True,
                                             enable_thinking=False)
        assert tokenizer.encode(text, add_special_tokens=False) == row["input_ids"]
        ids = row["output_ids"]
        assert tokenizer.decode(ids, skip_special_tokens=True).strip() == row["output"]
        assert 0 < len(ids) <= row["cap"] and eos not in ids[:-1]
        assert (ids[-1] == eos and row["stop"] == "eos") or (ids[-1] != eos and len(ids) == row["cap"] and row["stop"] == "cap")
        marks[row["id"]] = {
            "old": mechanical(older["output"], added["status"]),
            "certified": mechanical(row["output"], added["status"]),
            "additional_input_tokens": len(row["input_ids"]) - len(older["input_ids"]),
            "old_generated_tokens": len(older["output_ids"]), "certified_generated_tokens": len(ids),
            "old_stop": older["stop"], "certified_stop": row["stop"],
        }
        variant = row["id"].rsplit("-", 1)[1]
        for_state = next(v for v in family["variants"] if v["id"] == variant)
        opaque = "C-" + hashlib.sha256(f"certificate-demo::{row['id']}".encode()).hexdigest()[:10]
        assert opaque not in key
        key[opaque] = row["id"]
        deck.append(request({**packet(family, for_state, cases["boundary"], "judge"),
                             "id": opaque, "answer": row["output"]}))
    random.Random(261119).shuffle(deck)
    out.mkdir()
    for name, obj in (("mechanical.json", marks), ("deck.json", deck), ("arm-key.json", key)):
        (out / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    audit(args.run, args.output)
