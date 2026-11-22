"""Test whether explicit slots preserve public details on all four receipts."""
import argparse
from contextlib import contextmanager
import json
from pathlib import Path
from unittest.mock import patch

import minurso_receipt_writer as base

HEADINGS = {
    "Adoption": "Fill each slot: original draft symbol -> adopted resolution symbol; tally for/against/abstaining; member not participating.",
    "Amendments": "For each of the two amendments fill three slots: symbol | distinct language it proposed | outcome and tally. "
                  "Preserve the number of years in the first and distinguish considering a monitoring expansion from authorizing one in the second.",
    "Algeria": "If received, give the national position on monitoring and connect the stated penholder complaint to the participation decision. "
               "If the national account is absent, write 'National account not received.'",
    "Switzerland": "If received, identify the national vote on each amendment by symbol and the reason given for the second. "
                   "If the national account is absent, write 'National account not received.'",
    "Authority": "Fill three slots: date of mandate extension | specific OHCHR access step requested | whether monitoring functions were added.",
}
SYSTEM = (
    "Write a neutral historical record using the delivered evidence. Write five lines using the requested headings. "
    "Fill every applicable slot on every line with the shortest exact wording that preserves what happened. "
    "Use the original instrument symbols and the numbers in the evidence. End each substantive line with its evidence IDs in brackets. "
    "Treat a proposal to consider a change and an adopted change as different acts. No introduction or additional notes. At most 155 words."
)
BASE_LOCKS = base.locks


def locks():
    path = Path(__file__)
    return {**BASE_LOCKS(), path.name: base.runner.digest(path)}


@contextmanager
def parameters():
    with patch.multiple(base, HEADINGS=HEADINGS, SYSTEM=SYSTEM, locks=locks):
        yield


def compare(directory, annotation):
    import minurso_receipt_scores as review

    with patch.object(review, "locks", locks):
        receipts = review.add_readout(directory, annotation)
    return {"scope": annotation["scope"], "transcript_sha256": annotation["transcript_sha256"],
            "receipts": receipts, "rollout": review.rollout(receipts)}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "replay", "score"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    cli.add_argument("--annotations", type=Path)
    args = cli.parse_args()
    with parameters():
        if args.mode == "run":
            if args.model is None:
                cli.error("run requires --model")
            base.run(args.model, args.directory)
        elif args.mode == "replay":
            print(json.dumps(base.replay(args.directory), ensure_ascii=False, indent=2))
        else:
            if args.annotations is None:
                cli.error("score requires --annotations")
            print(json.dumps(compare(args.directory, json.loads(args.annotations.read_text())), indent=2))
