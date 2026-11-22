"""Revise only the comparison after scoring the first pass."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import writer

original_locks = writer.locks
original_build = writer.build
HERE = writer.HERE


def build():
    old, = [r for r in original_build() if r["id"] == "overlap"]
    system, prompt = old["messages"]
    facts = json.loads(prompt["content"])["source_material"]
    assert all("transition" in facts[k] for k in ("CHINA", "A3"))
    assert "abstained" in facts["CHINA"] and "supported adoption" in facts["A3"]
    body = {"task": "Write two short ordinary sentences. Sentence 1 states the common position. "
                    "Sentence 2 records each side's vote. End with [VOTE, CHINA, A3].",
            "authorized_comparison": {
                "common_position": "China and the A3 backed international assistance alongside a Haitian political transition.",
                "vote_by_party": {"China": "abstained", "the three African Council members": "voted in favour"},
            }}
    return [{**old, "messages": [system, {**prompt, "content": json.dumps(body, ensure_ascii=False)}]}]


def locks():
    return {**original_locks(), Path(__file__).name: writer.runner.digest(Path(__file__)),
            "prior_trace": writer.runner.digest(HERE / "evidence/transcript.jsonl")}


def episode(generate):
    return [{"family": "haiti-writer-transfer", "final": generate(build())}]


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "replay"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        with patch.multiple(writer.runner, episode=episode, locks=locks):
            writer.runner.run(args.model, args.directory)
    else:
        with patch.multiple(writer, build=build, locks=locks):
            print(json.dumps({"records": len(writer.replay(args.directory)), "exact_replay": True}))
