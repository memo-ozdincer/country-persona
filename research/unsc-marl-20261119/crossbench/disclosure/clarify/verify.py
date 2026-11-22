"""Rebuild every prompt, adjudication, visibility boundary and aggregate."""
import argparse
from collections import Counter
import json
from hashlib import sha256
from pathlib import Path

from transformers import AutoTokenizer

from probe import CAP, CONTINUATIONS, evaluate, experiment, locks, serialize


def verify(path):
    launch = json.loads((path / "launch.json").read_text())
    complete = json.loads((path / "complete.json").read_text())
    transcript = (path / "transcript.jsonl").read_bytes()
    assert sha256(transcript).hexdigest() == complete["transcript_sha256"]
    assert launch["optimizer_updates"] == complete["optimizer_updates"] == 0
    assert {p.name: sha256(p.read_bytes()).hexdigest() for p in locks()} == launch["sha256"]
    rows = [json.loads(line) for line in transcript.splitlines()]
    pending = {row["id"]: row for row in rows}
    assert len(pending) == len(rows) == 38
    tok = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")

    def generate(specs):
        verified = {}
        for expected, role, menu, arm, option in specs:
            row = pending.pop(expected["id"])
            assert all(row[k] == value for k, value in expected.items())
            assert row["role"] == role and row["query"] == option
            rendered = tok.apply_chat_template(row["messages"], tokenize=False, add_generation_prompt=True,
                                               enable_thinking=False)
            assert tok.encode(rendered, add_special_tokens=False) == row["input_ids"]
            tail = row["output_ids"]
            assert 0 < len(tail) <= CAP and eos not in tail[:-1]
            assert tail[-1] == eos or len(tail) == CAP
            assert tok.decode(tail, skip_special_tokens=True).strip() == row["output"]
            assert evaluate(row["output"], row["id"], role, menu, arm, option) == row["judgment"]
            verified[row["id"]] = row
        return verified

    result = experiment(generate)
    assert not pending and result == json.loads((path / "metrics.json").read_text())
    by_id = {r["id"]: r for r in rows}
    episodes = {}
    for key in result:
        family, variant, arm = key.split("/")
        episode = [by_id[f"{family}/shared/open-0"], by_id[f"{family}/{variant}/open-1"]]
        episode += [by_id[f"{key}-{step}"] for step in range(CONTINUATIONS)]
        episodes[key] = {
            "cap_hits": sum(r["output_ids"][-1] != eos for r in episode),
            "continuation_speaker_counts": dict(Counter(r["role"] for r in episode[2:])),
            "continuation_judgments": dict(Counter(r["judgment"]["kind"] for r in episode[2:])),
        }
    return {"records": len(rows), "optimizer_updates": 0, "transcript_sha256": complete["transcript_sha256"],
            "certificates": {k: v["first_certified_after_continuation"] for k, v in result.items()},
            "episode_checks": episodes}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    print(serialize(verify(parser.parse_args().run)))
