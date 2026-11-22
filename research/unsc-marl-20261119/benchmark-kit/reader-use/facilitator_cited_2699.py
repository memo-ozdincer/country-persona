"""Select exact source sentence IDs for the three Haiti delegation cards."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_preflight_2699 as archive

HERE = archive.HERE
EVIDENCE = HERE / "facilitator-cited-2699-evidence"
FAMILY = "facilitator-cited-2699"
SOURCE = archive.source
RUNNER = archive.RUNNER
ORDERS = ((3, 1, 4, 0, 2), (2, 4, 0, 1, 3))
SYSTEM = (
    "Select documentary evidence for three claims about the assigned delegation. "
    "For each claim, return the single sentence's letter only if the sentence supports the full claim "
    "with the stated actor, scope and timing. Use X when no supplied sentence establishes it. "
    "A related statement or overlapping terms are not enough. Return exactly three tokens in claim order "
    "separated by single spaces. Example format: B X A. Do not repeat the claim or add punctuation."
)


def decks():
    return json.loads((EVIDENCE / "decks.json").read_text())


def cases():
    for name, deck in decks().items():
        assert tuple(deck["statements"])[:3] == tuple(deck["witnesses"])
        for group, orders in (("full", ORDERS), ("withheld", ORDERS), ("foil", ORDERS[:1])):
            for i, order in enumerate(orders):
                names = tuple(deck["statements"])
                contents = [names[j] for j in order if group != "withheld" or names[j] != deck["withheld"]]
                registry = {chr(65 + j): label for j, label in enumerate(contents)}
                choices = {key: deck["statements"][label] for key, label in registry.items()}
                claims = list(deck["claims"])
                expected = [next((k for k, label in registry.items() if label == witness), "X")
                            for witness in deck["witnesses"]]
                if group == "foil":
                    claims[deck["foil_slot"]] = deck["foil"]
                    expected[deck["foil_slot"]] = "X"
                yield f"{name}/{group}/{i}", {"assigned_speaker": deck["speaker"], "claims": claims,
                                               "source_sentences": choices}, registry, expected


def requests():
    for key, view, _, _ in cases():
        yield SOURCE.live.prompt(key, 16, SYSTEM, view)


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(requests()))}]


def pins():
    paths = (Path(__file__).resolve(), EVIDENCE / "decks.json", EVIDENCE / "protocol.md",
             archive.EVIDENCE / "results.json", archive.EVIDENCE / "joins.json")
    return {**archive.pins(), **{str(p.relative_to(HERE.parents[1])): RUNNER.digest(p) for p in paths}}


def verify(directory):
    previous = SOURCE.live.common.reused.previous.prior
    with patch.multiple(previous, local=requests, audits=lambda _: (), syntheses=lambda _: (), pins=pins, FAMILY=FAMILY):
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
