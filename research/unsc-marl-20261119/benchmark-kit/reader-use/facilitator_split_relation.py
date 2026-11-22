"""Classify source support and incompatibility with separate typed checks."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_typed_clarification as typed
import facilitator_event_transfer as transfer

HERE = typed.HERE
runner = typed.runner
protocol = typed.protocol
CONTEXT = typed.TASK
CHECKS = {
    "support": (
        " Does the official card establish the exact assertion as written? A correct actor, act and scope are required.",
        ("The assertion is established.", "The assertion remains unestablished."),
    ),
    "incompatibility": (
        " Could the exact assertion and the fact documented in the card both be true? Select incompatible only "
        "if the card rules it out. An unmentioned act, a related statement, or a narrower claim can leave it open.",
        ("The assertion conflicts with what the card explicitly records.", "The assertion could still be true or is unresolved."),
    ),
}


def items():
    yield from typed.items()
    for panel, _, predicate, _, cards in transfer.panels():
        for i, (speaker, passage) in enumerate(cards, 1):
            yield (panel, f"S{i}", "direct"), {"assertion": f"{speaker} {predicate}.", "source": passage}


def prompts():
    for key, payload in items():
        for check, (instruction, options) in CHECKS.items():
            for n, order in enumerate(((0, 1), (1, 0))):
                menu = {letter: options[slot] for letter, slot in zip("AB", order, strict=True)}
                yield {"observation": (*key, check, n), "legal": order, "messages": [
                    {"role": "system", "content": CONTEXT + instruction + " Return only the option letter."},
                    {"role": "user", "content": json.dumps(payload | {"options": menu}, ensure_ascii=False)},
                ]}
        if key[0].startswith(("abyei-", "central-african-republic-")):
            yield from protocol.encoded((*key, "three_way"), CONTEXT, payload, typed.OPTIONS)


def pins():
    paths = (Path(__file__), *(HERE.parents[1] / key for key in typed.pins() | transfer.pins()))
    return {str(p.resolve().relative_to(HERE.parents[1])): sha256(p.read_bytes()).hexdigest() for p in paths}


def read(directory):
    with patch.multiple(runner, observations=prompts, hashes=pins):
        raw = runner.read(directory)
    records = {}
    for key, _ in items():
        decisions = {}
        for check in CHECKS:
            votes = protocol.votes(raw, (*key, check), ("yes", "no"))
            decisions[check] = {"votes": votes, "stable_yes": protocol.stable(votes) == "yes"}
        positive = decisions["support"]["stable_yes"]
        negative = decisions["incompatibility"]["stable_yes"]
        relation = ("supports" if positive else "contradicts") if positive != negative else "unknown"
        if (*key, "three_way", 0) in raw:
            votes = protocol.votes(raw, (*key, "three_way"), typed.LABELS)
            decisions["three_way"] = {"votes": votes, "admitted": protocol.stable(votes) or "unknown"}
        records["/".join(key)] = {"admitted": relation, "checks": decisions,
                                  "conflicting_checks": positive and negative}
    return raw, records


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("run", "inspect"))
    p.add_argument("directory", type=Path)
    p.add_argument("--model", type=Path)
    args = p.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, observations=prompts, hashes=pins):
            runner.score(args.model, args.directory)
    else:
        print(json.dumps(read(args.directory)[1], indent=2))
