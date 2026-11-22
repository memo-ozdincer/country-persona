"""Run balanced prompt variations across the Resolution 2719 source cards."""
import argparse
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_measured_channel_replies as archive
import facilitator_measured_channel_score as scorer

HERE, RUNNER, fit = archive.HERE, archive.RUNNER, archive.fit
EVIDENCE = HERE / "facilitator-question-wording-evidence"
QUESTIONS = EVIDENCE / "questions.json"
FAMILY = "facilitator-question-wording-2719"


def local():
    texts = json.loads(QUESTIONS.read_text())
    for kind, card in product(range(4), range(1, 4)):
        question = texts["generic"][kind] if kind < 2 else texts["matched"][card - 1][kind - 2]
        yield fit.live.live.prompt(f"{kind}/{card}", 92, fit.live.prior_claims.SYSTEM,
            {"received_question": question, "authorized_source": archive.cards()[card - 1]["source"]})


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(local()))}]


def pins():
    files = (Path(__file__).resolve(), EVIDENCE / "protocol.md", QUESTIONS, archive.PACK,
             Path(RUNNER.__file__).resolve(), Path(fit.live.prior_claims.__file__).resolve(),
             archive.EVIDENCE / "admission.json", archive.EVIDENCE / "fits.json")
    return {str(p.relative_to(HERE.parents[1])): RUNNER.digest(p) for p in files}


def verify(directory):
    previous = fit.live.live.common.reused.previous.prior
    with patch.multiple(previous, local=local, audits=lambda _: (), syntheses=lambda _: (), pins=pins, FAMILY=FAMILY):
        return previous.read(directory)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("run", "blind", "score"))
    p.add_argument("directory", type=Path)
    p.add_argument("--model", type=Path)
    args = p.parse_args()
    if args.mode == "run":
        with patch.multiple(RUNNER, episode=episode, locks=pins):
            RUNNER.run(args.model, args.directory)
    else:
        rows = verify(args.directory)
        output = (scorer.blind(rows) if args.mode == "blind"
                  else scorer.score(rows, json.loads((args.directory / "review.json").read_text())))
        print(json.dumps(output, ensure_ascii=False, indent=2))
