"""Collect the full held-out documentary channel matrix on Resolution 2719."""
import argparse
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_resolution_2719 as dossier
import facilitator_channel_fit as fit

HERE, RUNNER = dossier.HERE, dossier.RUNNER
EVIDENCE = HERE / "facilitator-measured-channel-evidence"
PACK = EVIDENCE / "challenge.json"
FAMILY = "facilitator-measured-channel-2719"


def cards():
    return json.loads(PACK.read_text())


def local():
    items = cards()
    questions = ("", *(card["question"] for card in items))
    for q, c in product(range(4), range(1, 4)):
        yield fit.live.live.prompt(f"{q}/{c}", 92, fit.live.prior_claims.SYSTEM,
                                   {"received_question": questions[q], "authorized_source": items[c - 1]["source"]})


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(local()))}]


def pins():
    files = (Path(__file__).resolve(), EVIDENCE / "protocol.md", PACK, dossier.PACKET, Path(RUNNER.__file__).resolve(),
             Path(fit.live.prior_claims.__file__).resolve())
    return {str(p.relative_to(HERE.parents[1])): RUNNER.digest(p) for p in files}


def verify(directory):
    previous = fit.live.live.common.reused.previous.prior
    with patch.multiple(previous, local=local, audits=lambda _: (), syntheses=lambda _: (), pins=pins, FAMILY=FAMILY):
        return previous.read(directory)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("run", "verify"))
    p.add_argument("directory", type=Path)
    p.add_argument("--model", type=Path)
    args = p.parse_args()
    if args.mode == "run":
        with patch.multiple(RUNNER, episode=episode, locks=pins):
            RUNNER.run(args.model, args.directory)
    else:
        rows = verify(args.directory)
        print(json.dumps({"verified_generations": len(rows)}, indent=2))
