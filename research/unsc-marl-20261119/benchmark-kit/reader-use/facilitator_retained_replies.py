"""Collect the missing generic candidates for the matched two-draft comparison."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_2504_routing as prior

HERE, RUNNER = prior.HERE, prior.RUNNER
EVIDENCE = HERE / "facilitator-retained-replies-evidence"
FAMILY = "facilitator-retained-replies-2504"


def local():
    path = HERE / "facilitator-question-wording-evidence/questions.json"
    generic = json.loads(path.read_text())["generic"][1]
    for c, payload in enumerate(prior.cards(), 1):
        yield prior.fit.live.live.prompt(f"0/{c}", 92, prior.fit.live.prior_claims.SYSTEM,
             {"received_question": generic, "authorized_source": payload["source"]})


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(local()))}]


def pins():
    paths = (Path(__file__).resolve(), EVIDENCE / "protocol.md", Path(prior.__file__).resolve(), prior.CHALLENGE,
             prior.case.PACKET, prior.EVIDENCE / "admission.json", Path(RUNNER.__file__).resolve(),
             HERE / "facilitator-question-wording-evidence/questions.json")
    return {str(p.relative_to(HERE.parents[1])): RUNNER.digest(p) for p in paths}


def verify(directory):
    old = prior.fit.live.live.common.reused.previous.prior
    with patch.multiple(old, local=local, audits=lambda _: (), syntheses=lambda _: (), pins=pins, FAMILY=FAMILY):
        return old.read(directory)


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
        if args.mode == "blind":
            with patch.object(prior.review.study, "cards", prior.cards):
                output = prior.review.blind(rows)
        else:
            output = prior.review.score(rows, json.loads((args.directory / "review.json").read_text()))
        print(json.dumps(output, ensure_ascii=False, indent=2))
