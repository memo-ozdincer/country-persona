"""Rerun the frozen Venezuela chair with evidence-specific record fields."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import duplicate_card_score as score
import duplicate_card_writer as original
import source_record_run as runner

BASE_SUITE = original.suite
BASE_LOCKS = original.locks
PUBLIC_FIELDS = (
    "Use at most 120 words. Write one compact record in the following order. "
    "First give one vote sentence for each draft. For each sentence retain the exact draft symbol, sponsor, "
    "three vote counts and distinct non-adoption reason from its VOTE source. "
    "Next give one sentence comparing the political proposals. Include the election observation and named "
    "dialogue mechanism. Give one sentence comparing the two approaches to humanitarian assistance. "
    "Write the available national statements using the source-specific fields below. "
    "Then state whether either failed draft conferred authority and give a short labeled analytical suggestion. "
    "Cite evidence IDs in brackets. Use only the supplied sources. Skip absent national statements."
)
NATIONAL_FIELDS = {
    "CHAIR": (
        "Give one sentence from CHAIR with the speaker, the capacity in which he announced the results, "
        "and the country's separate national vote on each draft."
    ),
    "INDONESIA": (
        "Give one sentence from INDONESIA with both national votes, what scope of dialogue it urged, "
        "and who it called on to accept whose good offices."
    ),
}


def suite():
    for request in BASE_SUITE():
        payload = json.loads(request["messages"][-1]["content"])
        payload["task"] = " ".join([
            PUBLIC_FIELDS, *(note for card, note in NATIONAL_FIELDS.items() if card in payload["evidence"])
        ])
        request["messages"][-1]["content"] = json.dumps(payload, ensure_ascii=False)
        yield request


def locks():
    here = Path(__file__).resolve()
    return {**BASE_LOCKS(), str(here.relative_to(here.parent.parent)): runner.digest(here)}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "replay", "review-deck", "score"))
    cli.add_argument("directory", type=Path, nargs="?")
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "check":
        print(json.dumps({"suite": list(suite()), "sha256": locks()}, indent=2, ensure_ascii=False))
    elif args.directory is None:
        cli.error("directory is required")
    elif args.mode == "run":
        if args.model is None:
            cli.error("--model is required")
        with patch.multiple(original, suite=suite, locks=locks):
            with patch.multiple(runner, locks=locks, episode=original.episode):
                runner.run(args.model, args.directory)
    elif args.mode == "replay":
        with patch.multiple(original, suite=suite, locks=locks):
            print(json.dumps(original.replay(args.directory), indent=2))
    else:
        with patch.object(score, "suite", suite):
            result = score.score(args.directory) if args.mode == "score" else score.bundle(args.directory)[0]
        print(json.dumps(result, indent=2, ensure_ascii=False))
