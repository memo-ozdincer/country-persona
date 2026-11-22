"""Edit a single qualification in two already observed writing contexts."""
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import run_protected as original

audit, runner = original.audit, original.runner
PROTOCOL = HERE / "protocol.json"
EVIDENCE = HERE / "evidence"


def requests():
    edits = audit.read(PROTOCOL)["edits"]
    for row in original.requests():
        if row["id"] not in edits:
            continue
        edit = edits[row["id"]]
        system, user = row["messages"]
        source = json.loads(user["content"])
        note = source["supplement"]["note"]
        assert note.count(edit["replace"]) == 1
        source["supplement"]["note"] = note.replace(edit["replace"], edit["with"])
        serialized = json.dumps(source, ensure_ascii=False)
        assert user["content"].replace(edit["replace"], edit["with"], 1) == serialized
        yield {**row, "messages": [system, {**user, "content": serialized}]}


def episode(generate):
    prompts = list(requests())
    assert len(prompts) == 2
    return [{"family": "bosnia2604-qualification-swap", "final": generate(prompts)}]


def pins():
    return {**original.pins(), "qualification-swap/run_swap.py": runner.digest(Path(__file__)),
            "qualification-swap/protocol.json": runner.digest(PROTOCOL),
            "protected-record/evidence/transcript.jsonl": runner.digest(original.EVIDENCE / "transcript.jsonl")}


if __name__ == "__main__":
    with patch.multiple(runner, episode=episode, locks=pins):
        runner.run(original.MODEL, EVIDENCE)
