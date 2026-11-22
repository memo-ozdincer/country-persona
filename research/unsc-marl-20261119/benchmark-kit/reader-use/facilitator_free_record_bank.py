"""Generate all receipt subsets of Resolution 2699 as unconstrained final prose."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_preflight_2699 as source

HERE = source.HERE
EVIDENCE = HERE / "facilitator-free-record-bank-evidence"
FAMILY = "facilitator-free-record-bank-2699"
RUNNER = source.RUNNER
SYSTEM = (
    "Write a concise factual Security Council meeting record in at most 285 words. "
    "Preserve the date, decision, vote, sponsors, institutions, legal force and qualifications in the Council facts. "
    "Cover all material claims in the available national source cards, attributing them to their own delegation. "
    "If both abstainers' cards are available, explicitly compare what they shared and where their requests differ. "
    "Use only the supplied documents. Treat a missing card as missing evidence about the delegation's rationale. "
    "Keep the Council's authority separate from each delegation's views. Return only the meeting record."
)


def local():
    packet = source.packet()
    for mask in range(8):
        remarks = {c["speaker"]: c["source"] for i, c in enumerate(packet["cards"]) if mask & (1 << i)}
        yield source.source.live.prompt(str(mask), 432, SYSTEM,
            {"public_council_facts": packet["public"], "authorized_national_cards": remarks})


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(local()))}]


def pins():
    files = (Path(__file__).resolve(), EVIDENCE / "protocol.md", source.PACKET, Path(RUNNER.__file__))
    return {str(p.relative_to(HERE.parents[1])): RUNNER.digest(p) for p in files}


def verify(directory):
    previous = source.source.live.common.reused.previous.prior
    with patch.multiple(previous, local=local, audits=lambda _: (), syntheses=lambda _: (), pins=pins, FAMILY=FAMILY):
        return previous.read(directory)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "verify"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        assert len(list(local())) == 8
        with patch.multiple(RUNNER, episode=episode, locks=pins):
            RUNNER.run(args.model, args.directory)
    else:
        print(json.dumps({"verified_generations": len(verify(args.directory))}))
