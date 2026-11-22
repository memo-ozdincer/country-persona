"""Rerun exactly the four public-state prompts with an explicit extraction contract."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import live

SUFFIX = (
    ' The phrase after "fictional constraint:" on the private card has the form FIELD = VALUE. '
    'Use only the text left of "=" as the field string and only the text right of "=" as the value string, '
    'without the final period or surrounding spaces. For example, "color = teal." becomes '
    '{"field":"color","value":"teal"}.'
)


def requests():
    archived = live.r.e.read(HERE.parent / "requests.json")
    for row in archived:
        row["request"]["messages"][0]["content"] += SUFFIX
    return archived


def pins():
    paths = (Path(__file__), HERE / "protocol.md", HERE / "requests.json", HERE.parent / "requests.json",
             HERE.parent / "evidence/complete.json", live.RECORD / "marks.json",
             live.r.e.HERE / "release.json")
    return {str(path.relative_to(live.r.env.CHAIR.ROOT)): sha256(path.read_bytes()).hexdigest()
            for path in paths}


def collect(generate, directory):
    frozen = live.r.e.read(HERE / "requests.json")
    assert frozen == requests()
    for row in frozen:
        reply = generate(row["request"])
        live.collector.suite.append(directory / "records.jsonl", {**row, "response": reply})
    (directory / "followup-lock.json").write_text(json.dumps(pins(), indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("deck", "run"))
    if parser.parse_args().mode == "deck":
        live.r.e.emit(requests())
    else:
        roster = {case["id"]: case for _, case, *_ in live.sources()}
        with patch.object(live.collector.suite, "collect", collect), patch.object(live.collector, "roster", return_value=roster):
            live.collector.run(HERE / "evidence")
