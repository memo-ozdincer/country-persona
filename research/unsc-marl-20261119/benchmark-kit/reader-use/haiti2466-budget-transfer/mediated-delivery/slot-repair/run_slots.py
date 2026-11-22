"""Test whether an explicit positional instruction preserves the one remaining field."""
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import run_delivery as prev

EVIDENCE = HERE / "evidence"
FAMILY = "haiti2466-admission-slot-repair"
SYSTEM = (
    "Match each requested field with an offered passage ID from your source. The peer question is context only. "
    "Return two bare lines in the fixed slot order. Line one answers field 1 and line two answers field 2. "
    "A missing field still occupies its own line with EMPTY. Never shift an ID up or down. "
    "For an unsupported first field and a second field supported by K9, the two lines are EMPTY then K9. "
    "For a first field supported by K9 and an unsupported second field, the lines are K9 then EMPTY. "
    "K9 is only an example. Use the offered IDs only. Output just the two ID or EMPTY lines, with no numbering."
)


def requests():
    return [{**row, "messages": [{**row["messages"][0], "content": SYSTEM}, row["messages"][1]]}
            for row, _ in prev.cases() if row["id"].startswith("withheld/")]


def episode(generate):
    return [{"family": FAMILY, "final": generate(requests())}]


def pins():
    return {**prev.pins(), "slot-repair/protocol.md": prev.runner.digest(HERE / "protocol.md"),
            "slot-repair/run_slots.py": prev.runner.digest(Path(__file__))}


if __name__ == "__main__":
    with patch.multiple(prev.runner, episode=episode, locks=pins):
        prev.runner.run(prev.base.MODEL, EVIDENCE)
