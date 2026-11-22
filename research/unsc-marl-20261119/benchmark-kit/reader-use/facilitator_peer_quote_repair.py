"""Replay final writers after removing only matching outer quotation delimiters."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_peer_findings as prior

HERE = prior.HERE
OLD = HERE / "facilitator-peer-findings-evidence"
FAMILY = "facilitator-peer-quote-repair"
runner = prior.runner


def old_rows():
    transcript = OLD / "transcript.jsonl"
    complete = json.loads((OLD / "complete.json").read_text())
    assert runner.digest(transcript) == complete["transcript_sha256"]
    return {r["id"]: r for r in map(json.loads, transcript.read_text().splitlines())}


def normalized_requests():
    rows = old_rows()
    with patch.object(prior, "findings", wrapped_base):
        yield from prior.final_requests(rows)


# Cache the original function before the temporary patch in normalized_requests.
original_findings = prior.findings


def wrapped_base(row, source):
    label, divider, text = (piece.strip() for piece in row["output"].partition(","))
    if divider:
        for edge in ('\\"', '"'):
            if text.startswith(edge) and text.endswith(edge) and len(text) > 2 * len(edge):
                row = row | {"output": f"{label}, {text[len(edge):-len(edge)]}"}
                break
    return original_findings(row, source)


def requests():
    old = old_rows()
    for req in normalized_requests():
        if req["messages"] != old[req["id"]]["messages"]:
            yield req


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(requests()))}]


def pins():
    paths = prior.pins()
    for file in (Path(__file__), OLD / "launch.json", OLD / "complete.json", OLD / "transcript.jsonl"):
        paths[str(file.resolve().relative_to(HERE.parents[1]))] = runner.digest(file)
    return paths


def verify(directory):
    locked = pins()
    module = prior.transfer
    with patch.multiple(module, local=requests, audits=lambda _: (), syntheses=lambda _: (),
                        pins=lambda: locked, FAMILY=FAMILY):
        return module.read(directory)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("run", "verify"))
    p.add_argument("directory", type=Path)
    p.add_argument("--model", type=Path)
    args = p.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, episode=episode, locks=pins):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps({"verified": len(verify(args.directory))}))
