"""Run an attribution-focused prompt on the frozen matched receipt masks."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import natural_writer as n
import read_native as judge

ORIGINAL_SETUP = n.setup
OUT = HERE / "evidence"
SYSTEM = (
    "Write a standalone Council record from the supplied blocks. Use 125 to 140 words, maximum 150. "
    "Start with the date, draft symbol, sponsor, adopted instrument, full vote tally, and abstainers. "
    "State the mandate end date and the operative conditions on independence, permission and coordination. "
    "Then report each supplied national position in its own attributed clause. "
    "Retain qualifiers such as some or incomplete when present. "
    "Base any overlap or difference on the specific subject that both cited delegations discuss. "
    "Keep support for the mission separate from endorsement of the adopted text or any particular provision. "
    "Omit claims about national positions when their source is missing. Return only the record."
)


def setup():
    witness, case, requests = ORIGINAL_SETUP()
    for request in requests.values():
        request["messages"][0]["content"] = SYSTEM
    return witness, case, requests


def plan():
    original = n.read(HERE.parent / "plan.json")
    _, _, requests = setup()
    for row in original["requests"]:
        request = requests[row["mask"]]
        assert request["messages"][1:] == row["request"]["messages"][1:]
        assert request["max_output_tokens"] == row["request"]["max_output_tokens"]
    paths = (Path(__file__), HERE / "protocol.md", HERE.parent / "plan.json")
    return {"requests": [{"mask": mask, "request": row} for mask, row in requests.items()],
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in paths}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "packets", "verify", "score"))
    mode = parser.parse_args().mode
    with patch.multiple(n, setup=setup, HERE=HERE, OUT=OUT, plan=plan):
        if mode == "run":
            with patch.object(n.base.suite, "collect", n.collect), patch.object(
                    n.base, "roster", return_value={"matched-unifil-attributed-writer": None}):
                n.base.run(OUT)
        else:
            value = {"plan": plan, "packets": lambda: judge.packets()[1],
                     "verify": judge.verify, "score": judge.score}[mode]()
            print(json.dumps(value, ensure_ascii=False, indent=2))
