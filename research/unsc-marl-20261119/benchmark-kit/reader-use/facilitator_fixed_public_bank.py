"""Preserve the Council decision while generating the national account."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_free_record_bank as free

HERE = free.HERE
EVIDENCE = HERE / "facilitator-fixed-public-bank-evidence"
FAMILY = "facilitator-fixed-public-bank-2699"
RUNNER = free.RUNNER
SYSTEM = (
    "Write just the national accounts for a factual Security Council meeting record. "
    "The public decision and vote are already recorded and your text will be appended to them. "
    "Use only the supplied national cards and attribute claims to the speaker on each card. "
    "Preserve qualifications and requested conditions. Ecuador and the United States sponsored the draft. "
    "China and Russia were the two abstainers. If both their sources are available, explicitly identify "
    "the concern they shared and distinguish what each asked for. "
    "Do not add or infer the rationale of a delegation with no card. "
    "Return plain prose, at most 140 words."
)


def public_anchor():
    return json.loads((free.source.EVIDENCE / "results.json").read_text())["rendered_record_bank"][0]


def local():
    for row in free.local():
        if row["id"] == "0":
            continue
        cards = json.loads(row["messages"][-1]["content"])["authorized_national_cards"]
        yield free.source.source.live.prompt(row["id"], 220, SYSTEM, {"authorized_national_cards": cards})


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(local()))}]


def pins():
    files = (Path(__file__).resolve(), EVIDENCE / "protocol.md", free.source.PACKET,
             free.source.EVIDENCE / "results.json", Path(RUNNER.__file__), Path(free.__file__),
             free.EVIDENCE / "rubric.json")
    return {str(p.relative_to(HERE.parents[1])): RUNNER.digest(p) for p in files}


def verify(directory):
    previous = free.source.source.live.common.reused.previous.prior
    with patch.multiple(previous, local=local, audits=lambda _: (), syntheses=lambda _: (), pins=pins, FAMILY=FAMILY):
        return previous.read(directory)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "verify"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        assert len(list(local())) == 7
        with patch.multiple(RUNNER, episode=episode, locks=pins):
            RUNNER.run(args.model, args.directory)
    else:
        print(json.dumps({"verified_generations": len(verify(args.directory))}))
