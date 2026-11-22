"""Expose only the selected grade to the reporting model."""
import argparse
from pathlib import Path
from unittest.mock import patch

import warrant_live as base

EVIDENCE = base.EVIDENCE / "authorized-only"
TASK = (
    "Transcribe the authorized grade from the input fields. Output exactly one line using this template: "
    "{delegate} reports grade {grade} for {package}. Replace each placeholder with its field value. "
    "Keep the period. Output only the line, with no quotation marks or additional text."
)
original_pins = base.pins


def note(identifier, fact, cards, request=None):
    side, slot, grade = fact
    assert cards[side][slot] == grade
    return base.prompt(identifier, 25, TASK, {"delegate": f"D{side+1}", "package": base.fit.PACKAGES[slot],
                                              "grade": grade})


def pins():
    return {**original_pins(), Path(__file__).name: base.runner.digest(Path(__file__)),
            "authorized_only_protocol": base.runner.digest(EVIDENCE / "protocol.md")}


def verify(directory):
    with patch.multiple(base, note=note, pins=pins):
        return base.verify(directory)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "verify"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        with patch.multiple(base, note=note, pins=pins):
            with patch.multiple(base.runner, episode=base.episode, locks=pins):
                base.runner.run(args.model, args.directory)
    else:
        print({"verified_generations": len(verify(args.directory))})
