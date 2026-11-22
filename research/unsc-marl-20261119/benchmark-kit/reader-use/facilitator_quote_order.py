"""Pair the original witness prompt with the same prompt asking for the evidence first."""
import argparse
from hashlib import sha256
from pathlib import Path
from unittest.mock import patch

import facilitator_event_transfer as held
import facilitator_split_relation as prior
import facilitator_witness as witness

HERE = witness.HERE
runner = witness.runner
base = held.chair
CAP = witness.CAP
FAMILY = "facilitator-quote-order"
ARMS = ("relation_first", "quote_first")


def requests():
    first = witness.requests()[0]["messages"][0]["content"]
    revised = first.replace("'supports|EXACT SOURCE WORDS' or 'contradicts|EXACT SOURCE WORDS'",
                            "'EXACT SOURCE WORDS|supports' or 'EXACT SOURCE WORDS|contradicts'")
    assert first != revised
    for key, body in prior.items():
        panel, sid, mode = key
        payload = {"claim": body["assertion"], "source": body["source"]}
        if "peer_question" in body:
            payload["peer_question"] = body["peer_question"]
        for arm, task in zip(ARMS, (first, revised), strict=True):
            if mode == "asked":
                task += " Use the optional question to focus on the relevant scope. The source itself determines the relation."
            yield held.prompt(f"{panel}/{sid}/{mode}/{arm}", CAP, task, payload)


def episode(generate):
    records = {}
    wanted = list(requests())
    for start in range(0, len(wanted), 12):
        records.update(generate(wanted[start:start+12]))
    return [{"family": FAMILY, "final": records}]


def pins():
    paths = (Path(__file__), *(HERE.parents[1] / name for name in prior.pins() | witness.hashes()))
    return {str(p.resolve().relative_to(HERE.parents[1])): sha256(p.read_bytes()).hexdigest() for p in paths}


def read(directory):
    archive = pins()
    with patch.multiple(base, pins=lambda: archive, requests=requests, CAP=CAP, FAMILY=FAMILY):
        return base.rows(directory)


def parse(output, source, arm):
    if arm == "quote_first" and "|" in output:
        quote, _, label = output.rpartition("|")
        output = f"{label}|{quote}"
    proposed, admitted, span = witness.read_witness(output, source)
    return proposed, admitted, span


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
        print("Verified", len(read(args.directory)), "generations")
