"""Repeat vote extraction with the same protocol described without placeholders."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_vote_channel as baseline

FAMILY = "facilitator-vote-channel-format"
TASK = baseline.TASK.replace(
    "respond yes|EXACT SOURCE WORDS, no|EXACT SOURCE WORDS, or abstain|EXACT SOURCE WORDS.",
    "write one line in two fields. First write the vote label (yes, no, or abstain), then a vertical bar, "
    "then the passage copied from the source."
)
assert TASK != baseline.TASK
prior = baseline.prior


def requests():
    for key, speaker, resolution, source, _ in baseline.cards():
        yield prior.transfer.prompt(key, baseline.CAP, TASK,
                                    {"delegation": speaker, "resolution": resolution, "source": source})


def episode(generate):
    wanted = list(requests())
    return [{"family": FAMILY, "final": generate(wanted[:8]) | generate(wanted[8:])}]


def pins():
    paths = baseline.pins()
    path = Path(__file__).resolve()
    paths[str(path.relative_to(prior.HERE.parents[1]))] = prior.runner.digest(path)
    return paths


def verify(directory):
    locked = pins()
    with patch.multiple(prior.chair, pins=lambda: locked, requests=requests, CAP=baseline.CAP, FAMILY=FAMILY):
        return prior.chair.rows(directory)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "score"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "run":
        with patch.multiple(prior.runner, episode=episode, locks=pins):
            prior.runner.run(args.model, args.directory)
    else:
        print(json.dumps(baseline.report(verify(args.directory)), indent=2))
