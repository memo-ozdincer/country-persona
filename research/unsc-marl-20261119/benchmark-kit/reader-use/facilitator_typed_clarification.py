"""Read and transmit local relations as constrained labels before assembly."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_clarification as prior
import facilitator_source_relation as judge

HERE = prior.HERE
SOURCE = HERE / "facilitator-clarification-evidence/final-records.json"
runner = judge.runner
protocol = judge.protocol
LABELS = judge.LABELS
OPTIONS = ("The official card establishes the assertion.", "The official card explicitly conflicts with the assertion.",
           "The official card leaves the assertion unresolved.")
TASK = (
    "Compare this delegation's own official card with the exact one-speaker assertion. Consider the peer question "
    "if present, then decide the assertion from the documentary card. If the actor, act or scope differs, the "
    "assertion remains unresolved unless the card directly rules it out. In particular, starting consultations, "
    "circulating the initial draft, and voting for a resolution are separate acts. A statement about one does not "
    "establish or contradict a statement about another. Check affirmative votes and abstentions explicitly."
)


def items():
    archive = prior.base.load(SOURCE)[prior.FAMILY]
    for panel, _, local, _, _, cards, _, target, _ in prior.source_inputs():
        for i, (speaker, passage) in enumerate(cards):
            payload = {"assertion": f"{speaker} {local}.", "source": passage}
            sid = f"S{i+1}"
            yield (panel, sid, "direct"), payload
            if i == target:
                yield (panel, sid, "asked"), payload | {"peer_question": archive[f"{panel}/question"]}


def prompts():
    for key, payload in items():
        yield from protocol.encoded(key, TASK, payload, OPTIONS)


def pins():
    files = (Path(__file__), Path(judge.__file__), Path(runner.__file__), SOURCE,
             *(HERE.parents[1] / p for p in prior.pins()))
    return {str(p.resolve().relative_to(HERE.parents[1])): sha256(p.read_bytes()).hexdigest() for p in files}


def read(directory):
    with patch.multiple(runner, observations=prompts, hashes=pins):
        raw = runner.read(directory)
    result = {}
    for key, _ in items():
        votes = protocol.votes(raw, key, LABELS)
        result["/".join(key)] = {"votes": votes, "admitted": protocol.stable(votes) or "unknown",
                                 "option_mass": [raw[(*key, i)]["legal_mass"] for i in range(2)]}
    return raw, result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "score"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, observations=prompts, hashes=pins):
            runner.score(args.model, args.directory)
    else:
        print(json.dumps(read(args.directory)[1], indent=2))
