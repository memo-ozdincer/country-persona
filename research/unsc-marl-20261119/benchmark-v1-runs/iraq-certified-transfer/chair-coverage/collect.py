"""Add a documentary checklist to the archived certified writer requests."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE.parent
sys.path.insert(0, str(ARCHIVE))
import format_replay as frozen

CHECKLIST = (
    " State how the Council voted as well as what it adopted. In the workshop section, "
    "describe how the options differ on consultation documentation. If there is an impasse, explain whether a "
    "different documentation choice could resolve the conflict. Say who could authorize a change to the mandate. "
    "Keep the fictional instructions attributed to their workshop roles."
)
BASE = frozen.COLLECTOR


def requests():
    deck = (ARCHIVE / "format-evidence" / "records.jsonl").read_text().splitlines()
    for key, request in frozen.requests():
        archived = json.loads(deck.pop(0))
        assert archived["id"] == key and archived["request"] == request
        request["messages"][0]["content"] += CHECKLIST
        yield key, request
    assert not deck


def pins():
    files = (
        Path(__file__), HERE / "protocol.md", ARCHIVE / "format-evidence/complete.json",
        ARCHIVE / "format-evidence/records.jsonl", ARCHIVE / "format-marks.json",
        frozen.E.HERE / "release.json", ARCHIVE.parents[1] / "benchmark/release.json",
    )
    return {str(p.relative_to(ARCHIVE.parents[1])): sha256(p.read_bytes()).hexdigest() for p in files}


def collect(generate, directory):
    for key, req in requests():
        BASE.suite.append(directory / "records.jsonl",
                          {"id": key, "request": req, "response": generate(req)})
    (directory / "format-lock.json").write_text(json.dumps(pins(), indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "verify", "deck"))
    args = parser.parse_args()
    if args.mode == "deck":
        frozen.E.emit([{"id": key, "request": request} for key, request in requests()])
        return
    directory = HERE / "evidence"
    if args.mode == "run":
        with patch.object(BASE.suite, "collect", collect), patch.object(BASE, "roster", frozen.transfer.cases):
            BASE.run(directory)
    else:
        with patch.object(frozen, "requests", requests), patch.object(frozen, "pins", pins):
            frozen.E.emit(frozen.verify(directory))


if __name__ == "__main__":
    main()
