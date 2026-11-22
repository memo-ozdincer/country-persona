"""Collect and score a matched reply matrix for Resolution 2504."""
import argparse
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_resolution_2504_provenance as case
import facilitator_measured_channel_replies as archive
import facilitator_measured_channel_score as review

HERE, RUNNER, fit = archive.HERE, archive.RUNNER, archive.fit
EVIDENCE = HERE / "facilitator-2504-routing-evidence"
CHALLENGE = EVIDENCE / "challenge.json"
FAMILY = "facilitator-2504-routing"


def cards():
    spec = json.loads(CHALLENGE.read_text())
    sources = case.packet()["cards"]
    for item, source in zip(spec["cards"], sources, strict=True):
        assert item["id"] == source["id"]
    return [{**c, **source, "source": source["source"].split(" (S/PV.", 1)[0].rstrip(".") + "."}
            for c, source in zip(spec["cards"], sources, strict=True)]


def local():
    sources = cards()
    questions = [json.loads(CHALLENGE.read_text())["generic"], *(c["question"] for c in sources)]
    for q, c in product(range(4), range(1, 4)):
        yield fit.live.live.prompt(f"{q}/{c}", 92, fit.live.prior_claims.SYSTEM,
            {"received_question": questions[q], "authorized_source": sources[c - 1]["source"]})


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(local()))}]


def pins():
    paths = (Path(__file__).resolve(), EVIDENCE / "protocol.md", CHALLENGE, case.PACKET,
             case.EVIDENCE / "provenance.json", archive.EVIDENCE / "fits.json",
             Path(RUNNER.__file__).resolve(), Path(fit.live.prior_claims.__file__).resolve())
    return {str(p.relative_to(HERE.parents[1])): RUNNER.digest(p) for p in paths}


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
        if args.mode == "blind":
            with patch.object(review.study, "cards", cards):
                output = review.blind(rows)
        else:
            output = review.score(rows, json.loads((args.directory / "review.json").read_text()))
        print(json.dumps(output, ensure_ascii=False, indent=2))
