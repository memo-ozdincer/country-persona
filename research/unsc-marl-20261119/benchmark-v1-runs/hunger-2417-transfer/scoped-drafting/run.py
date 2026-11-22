"""Change only the comparison writer's system instruction."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
sys.path.insert(0, str(PARENT))
import collect as base

SYSTEM = (
    "Write a factual comparison for a UN decision record from the two supplied "
    "items. Use one or two sentences, at most 42 words. Give the delegation's "
    "position with its exact degree of commitment, then say what the supplied "
    "Council provision actually does. Keep options separate from measures taken. "
    "If an option is merely recalled or considered, make clear it is not imposed "
    "by the supplied provision. Preserve meaningful timing distinctions, including "
    "whether reporting is continued, requested faster, or triggered by a condition. "
    "Attribute each action to its actual actor. If the items add no supported, "
    "specific comparison, respond exactly NONE. Use only the two supplied items."
)


def plan():
    original = base.plan()
    assert original == base.engine.e.read(PARENT/"plan.json")
    with patch.object(base, "SYSTEM", SYSTEM):
        spec = original | {"requests": base.requests(base.engine.e.read(PARENT/"case.json"))}
    for key, row in spec["requests"].items():
        assert original["requests"][key]["request"]["messages"][1] == row["request"]["messages"][1]
    spec["instruction_revision_sha256"] = {
        name: base.engine.run_suite.pin(HERE/name) for name in ("run.py", "protocol.md")
    }
    return spec


def packets(spec):
    case = base.engine.e.read(PARENT/"case.json")
    cards = {card["id"]: card for card in case["delegate"] + case["clause"]}
    outputs = base.engine.e.read(HERE/"verification.json")["outputs"]
    return [{"id": key, "sources": [cards[ident] for ident in sorted(row["pair"])],
             "comparison": outputs[key]["text"]} for key, row in spec["requests"].items()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify", "packets"))
    args = parser.parse_args()
    spec = plan()
    if args.mode != "plan":
        assert spec == base.engine.e.read(HERE/"plan.json")
    with patch.object(base, "HERE", HERE), patch.object(base, "OUT", HERE/"evidence"):
        if args.mode == "run":
            base.run(spec)
        else:
            base.engine.e.emit({"plan": lambda: spec, "verify": lambda: base.verify(spec),
                                "packets": lambda: packets(spec)}[args.mode]())


if __name__ == "__main__":
    main()
