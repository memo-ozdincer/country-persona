"""Compact-note control with the original Colombia dossier and final prompt."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import run as original

HERE = Path(__file__).resolve().parent
OPENING = ("Write 25–40 words of evidence notes, without headings or introductory text. "
           "Lead with the assigned statement and its speaker and represented party. "
           "Preserve one relevant distinction or condition for the chair. Use bracketed source IDs.")
REVISION = ("Revise in 25–40 words, without headings or introductory text. Lead with the assigned "
            "statement and its speaker and represented party. Preserve the qualification or correct a "
            "discrepancy if documentary evidence supports it. Note any unresolved authority if relevant. "
            "Cite documentary source IDs only.")


def episode(generate):
    def transform(batch):
        rows = []
        for row in batch:
            stage = row["id"].rsplit("/", 1)[-1]
            if stage == "chair":
                rows.append(row)
                continue
            role, prompt = row["messages"]
            body = json.loads(prompt["content"])
            task = body["task"]
            focus = task.split(" area. ", 1)[0] + " area. " if stage.startswith("opening") and " area. " in task else ""
            if stage.startswith("revision"):
                focus = task.split(" area in ", 1)[0] + " area. "
            body["task"] = focus + (OPENING if stage.startswith("opening") else REVISION)
            rows.append({**row, "messages": [role, {**prompt, "content": json.dumps(body, ensure_ascii=False)}]})
        return generate(rows)
    return original.episode(transform)


def locks():
    return {**original.locks(), Path(__file__).name: original.runner.digest(Path(__file__))}


def check():
    def fake(batch):
        return {row["id"]: {**row, "output": row["id"]} for row in batch}
    old, = original.episode(fake)
    new, = episode(fake)
    assert old["final"] == new["final"]
    changed = 0
    for group in ("openings", "revisions"):
        for key, item in new[group].items():
            old_row = old[group][key]
            for field in ("id", "cap", "seen", "evidence_ids"):
                assert old_row[field] == item[field]
            assert old_row["messages"][0] == item["messages"][0]
            prompt_old = json.loads(old_row["messages"][1]["content"])
            prompt_new = json.loads(item["messages"][1]["content"])
            assert prompt_old.pop("task") != prompt_new.pop("task")
            assert prompt_old == prompt_new
            changed += 1
    assert changed == 10
    return {"modified_note_prompts": changed, "identical_final_prompt_controls": 3,
            "maximum_output_tokens_per_arm": 716}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "replay"))
    cli.add_argument("directory", type=Path, nargs="?")
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "check":
        print(json.dumps(check(), indent=2))
    elif args.mode == "run":
        check()
        with patch.multiple(original.runner, episode=episode, locks=locks):
            original.runner.run(args.model, args.directory)
    else:
        with patch.multiple(original.replay, episode=episode, locks=locks):
            print(json.dumps(original.replay.replay(args.directory), indent=2))
