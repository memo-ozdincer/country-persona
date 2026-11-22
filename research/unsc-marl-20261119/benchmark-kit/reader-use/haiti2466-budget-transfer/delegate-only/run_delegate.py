"""Regenerate the two selected bodies using delegation-only lines."""
import sys
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import run_transfer as base

EVIDENCE = HERE / "evidence"
PROTOCOL = HERE / "protocol.json"
FAMILY = "haiti2466-delegate-only"


def requests():
    rows, _ = base.prompts()
    instruction = base.read(PROTOCOL)["instruction"]
    return [
        {**r, "messages": [{**r["messages"][0], "content": instruction}, r["messages"][1]]}
        for r in rows if r["id"].endswith("/selected")
    ]


def episode(generate):
    return [{"family": FAMILY, "final": generate(requests())}]


def pins():
    return {**base.pins(), "delegate-only/protocol.json": base.runner.digest(PROTOCOL),
            "delegate-only/run_delegate.py": base.runner.digest(Path(__file__))}


if __name__ == "__main__":
    with patch.multiple(base.runner, episode=episode, locks=pins):
        base.runner.run(base.MODEL, EVIDENCE)
