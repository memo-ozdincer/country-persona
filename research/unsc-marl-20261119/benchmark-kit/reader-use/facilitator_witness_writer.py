"""Generate a speaker field with or without the exact documentary witness."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_bound_fields as prior
import facilitator_event_transfer as held

base = prior.prior
HERE = prior.HERE
runner = prior.runner
CAP = prior.CAP
FAMILY = "facilitator-witness-writer"
ARMS = ("assertion", "witness")
DEV = HERE / "facilitator-witness-evidence/results.json"
TRANSFER = HERE / "facilitator-event-transfer-evidence/results.json"
TASK = (
    "Write one sentence of at most 21 words for the facilitator's brief. State what the named speaker actually "
    "said or did about the one-speaker assertion. Use the source. If an exact excerpt is supplied, focus on "
    "its decisive words and use the card to resolve any reference. Preserve qualifiers, tense, and vote polarity. "
    "An abstention establishes how a speaker voted. A delegate's support or vote never means the delegate "
    "adopted the measure. If the documentary record leaves part open, say so rather than completing the claim. "
    "Output the sentence alone without citations, quote labels, or a heading."
)


def fixtures():
    development = base.load(DEV)["reads"]
    transfer = base.load(TRANSFER)["readings"]
    combined = list(held.panels())
    for family, number in base.PANELS:
        claim, predicates, truth = base.transfer.PANELS[family][number]
        assert len(set(predicates)) == 1
        combined.append((f"{family}-{number}", claim, predicates[0], truth, base.transfer.packets()[family]))
    for panel, _, predicate, _, sources in combined:
        family, number = panel.rsplit("-", 1)
        for index, (speaker, source) in enumerate(sources):
            key = f"{panel}/S{index+1}"
            if key in transfer:
                entry = transfer[key]
                admitted, span = entry["quote"], entry["span"]
            else:
                entry = development[f"{family}/{number}/{index}"]
                admitted, span = entry["admitted"], entry["witness"]
            if admitted != "unknown":
                assert span and span in source
            yield key, {"speaker": speaker, "one_speaker_assertion": f"{speaker} {predicate}.",
                        "source": source}, span if admitted != "unknown" else None


def requests():
    for key, payload, span in fixtures():
        yield held.prompt(f"{key}/assertion", CAP, TASK, payload)
        if span:
            yield held.prompt(f"{key}/witness", CAP, TASK, payload | {"exact_excerpt": span})


def episode(generate):
    wanted = list(requests())
    records = {}
    for start in range(0, len(wanted), 12):
        records.update(generate(wanted[start:start+12]))
    return [{"family": FAMILY, "final": records}]


def pins():
    files = [Path(__file__), DEV, TRANSFER, Path(prior.__file__),
             *(HERE.parents[1] / k for k in held.pins())]
    return {str(p.resolve().relative_to(HERE.parents[1])): sha256(p.read_bytes()).hexdigest() for p in files}


def read(directory):
    checks = pins()
    with patch.multiple(base, pins=lambda: checks, requests=requests, CAP=CAP, FAMILY=FAMILY):
        return base.rows(directory)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "verify"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, episode=episode, locks=pins):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps({"verified_fields": len(read(args.directory))}))
