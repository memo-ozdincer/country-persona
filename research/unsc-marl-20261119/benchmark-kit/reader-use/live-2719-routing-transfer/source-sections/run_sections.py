"""Regenerate the six supplements using a source-by-source writing contract."""
import sys
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import live_transfer as live

EVIDENCE = HERE / "evidence"
PROTOCOL = HERE / "protocol.json"
FAMILY = "live-2719-source-sections"


def requests():
    config = live.load(PROTOCOL)
    prompts, routes = live.plan()
    assert routes == live.load(HERE.parent / "frozen-actions.json")
    return [{**row, "messages": [
        {**row["messages"][0], "content": config["instruction"]},
        row["messages"][1],
    ]} for row in prompts]


def episode(generate):
    return [{"family": FAMILY, "final": generate(requests())}]


def pins():
    return {**live.pins(), "source-sections/run_sections.py": live.runner.digest(Path(__file__)),
            "source-sections/protocol.json": live.runner.digest(PROTOCOL)}


if __name__ == "__main__":
    with patch.multiple(live.runner, episode=episode, locks=pins):
        live.runner.run(live.MODEL, EVIDENCE)
