"""Test a source-bound final-writing prompt on the same delivered documentary cards."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_requested_evidence as previous

HERE = previous.HERE
SOURCE = previous.EVIDENCE
FAMILY = "facilitator-authority-writer"
runner = previous.prior.runner
TASK = (
    "Write a public Council record in three sentences, at most 95 words. "
    "First, use [S0] to give the resolution number, adoption, all three vote counts, and the abstaining actor. "
    "Second, answer the editorial question using the delivered delegation card. State who said what, with the "
    "named actor, action, and its recipient, timing or qualifications when relevant. Cite that card. If the "
    "card cannot answer the question, say precisely which information is missing from the delivered evidence. "
    "Third, explain the Council's action on investigations using [S1]. Copy its operative verb exactly and "
    "state who would carry out these actions and within whose jurisdiction. Explain the procedural limit, "
    "such as whether the resolution itself decides individual liability. Check that Council action and "
    "delegation statements remain distinct. Use only delivered evidence."
)


def cases():
    for name, request, public, cards in previous.cases():
        for sid, text in cards.items():
            yield name, sid, {"editorial_question": request, "documentary_evidence": public | {sid: text}}


def requests():
    for name, sid, payload in cases():
        yield previous.prior.prompt(f"{name}/{sid}/final", 136, TASK, payload)


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(requests()))}]


def pins():
    files = (Path(__file__).resolve(), Path(previous.__file__), Path(runner.__file__),
             SOURCE / "packet.json", SOURCE / "rubric.md", SOURCE / "launch.json",
             SOURCE / "complete.json", SOURCE / "results.json", SOURCE / "grades.json")
    return {str(path.relative_to(HERE.parents[1])): runner.digest(path) for path in files}


def verify(directory):
    prior = previous.prior
    with patch.multiple(prior, local=requests, audits=lambda rows: (), syntheses=lambda rows: (),
                        pins=pins, FAMILY=FAMILY):
        return prior.read(directory)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "verify"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "verify":
        print(json.dumps({"verified_generations": len(verify(args.directory))}))
    else:
        with patch.multiple(runner, episode=episode, locks=pins):
            runner.run(args.model, args.directory)
