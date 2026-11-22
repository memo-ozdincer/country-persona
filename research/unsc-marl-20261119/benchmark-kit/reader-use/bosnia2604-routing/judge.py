"""Run the frozen model as an arm-masked benchmark judge."""
import json
from pathlib import Path
from unittest.mock import patch

import audit
from run import HERE, MODEL, PROTOCOL, runner

INSTRUCTIONS = HERE / "judge-instructions.md"
DIRECTORY = HERE / "judge-evidence"


def episode(generate):
    protocol = audit.read(PROTOCOL)
    inputs = {key: protocol[key] for key in ("public", "desks", "rubric", "release_failures")}
    requests = [
        {"id": item, "cap": 500,
         "messages": [{"role": "system", "content": INSTRUCTIONS.read_text()},
                      {"role": "user", "content": json.dumps({**inputs, "candidate": text}, ensure_ascii=False)}]}
        for item, text in audit.deck(audit.get_rows()).items()
    ]
    return [{"family": "bosnia2604-blinded-judge", "final": generate(requests)}]


def pins():
    files = (PROTOCOL, INSTRUCTIONS, audit.EVIDENCE / "transcript.jsonl", Path(__file__), Path(runner.__file__))
    return {p.name: runner.digest(p) for p in files}


if __name__ == "__main__":
    with patch.multiple(runner, episode=episode, locks=pins):
        runner.run(MODEL, DIRECTORY)
