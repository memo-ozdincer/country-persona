"""Replay one fully enveloping JSON fence without changing its selected IDs."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
from unittest.mock import patch

import compound_reply as c

n, e, w, g, HERE = c.n, c.e, c.w, c.g, c.HERE
PATTERN = re.compile(r"\A```json[ \t]*\r?\n([^\x60]+)\r?\n```\Z")


def unwrap(text):
    match = PATTERN.fullmatch(text)
    return match[1] if match else text


def run():
    raw = n.lines(c.OUT / "calls.jsonl")
    assert len(raw) == 1
    response = raw[0]["response"]
    assert c.expanded(response)["wire_status"] == "invalid_json"
    text = response["text"]
    parsed = response | {"text": unwrap(text)}
    assert parsed["text"] != text
    assert json.loads(c.expanded(parsed)["text"]) == ["7", "3", "5"]
    for invalid in ('before ' + text, text + '\nafter', '```json\n[99]\n```', '```json\n[73,73]\n```'):
        assert c.expanded(response | {"text": unwrap(invalid)})["text"] == "[]"
    return c.simulate(parsed) | {"raw_fenced_response": response, "format_replay": "single_json_fence_removed"}


def score():
    proof = HERE / "fenced-dispatch.json"
    data = run()
    assert json.loads(json.dumps(data)) == n.read(proof)
    read = n.read

    def select(path):
        return data if path == c.OUT / "dispatch.json" else read(path)

    with patch.object(n, "read", select), patch.object(w, "OUT", c.OUT), patch.object(g, "HERE", HERE):
        graded = g.run()
    del graded["sha256"]["dispatch.json"]
    for path in (proof, Path(__file__), HERE / "fence-protocol.md", c.OUT / "complete.json"):
        graded["sha256"][path.name] = sha256(path.read_bytes()).hexdigest()
    return graded


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("dispatch", "score"))
    e.emit(run() if cli.parse_args().mode == "dispatch" else score())
