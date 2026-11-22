"""Test two matched single-pass revisions of three archived Council records."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_matched_2593 as base

HERE = base.source.HERE
EVIDENCE = HERE / "facilitator-revise-2593-evidence"
FAMILY = "facilitator-revise-2593"
RUNNER = base.RUNNER
SYSTEM = (
    "Revise the draft into a faithful Security Council record of no more than 210 words. "
    "Keep all correct material details, restore missing material facts from the sources, and correct any claims "
    "without support. The Council's actions, sponsors, and delegation statements must remain distinct. "
    "Preserve the official force of each action. Link the two abstention explanations with evidence and "
    "do not infer which Russian concerns were part of the joint amendments. Use short sentences, compact "
    "lists within sentences, and no headings or introductory phrases. Return only the entire revised record."
)
STRUCTURE = (
    " Use no more than about 35 words for adoption, vote and sponsors, about 94 words for the operative "
    "provisions and about 80 words for the national accounts and their comparison. Before writing, map the "
    "operative facts to their actors and verbs. Keep Council demands, calls, commitments it notes, expectations "
    "and requests distinct. Check each named national reason against its own card. Fit the record by compressing "
    "phrasing, keeping the content of each list and the relationships between its elements."
)


def local():
    public, national = base.dossier()
    candidates = json.loads((base.EVIDENCE / "blind-finals.json").read_text())
    for alias, card in candidates.items():
        for variant, task in (("generic", SYSTEM), ("structured", SYSTEM + STRUCTURE)):
            yield base.source.live.prompt(f"{alias}/{variant}", 384, task,
                  {"draft": card["response"], "public_council_facts": public, "national_sources": national})


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(local()))}]


def pins():
    files = (Path(__file__).resolve(), EVIDENCE / "protocol.md", base.EVIDENCE / "blind-finals.json",
             base.EVIDENCE / "rubric.json", base.EVIDENCE / "launch.json")
    return {**base.pins(), **{str(p.relative_to(HERE.parents[1])): RUNNER.digest(p) for p in files}}


def verify(directory):
    previous = base.source.live.common.reused.previous.prior
    with patch.multiple(previous, local=local, audits=lambda _: (), syntheses=lambda _: (), pins=pins, FAMILY=FAMILY):
        return previous.read(directory)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "verify"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        with patch.multiple(RUNNER, episode=episode, locks=pins):
            RUNNER.run(args.model, args.directory)
    else:
        print(json.dumps({"verified_generations": len(verify(args.directory))}))
