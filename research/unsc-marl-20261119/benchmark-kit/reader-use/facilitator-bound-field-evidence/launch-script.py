"""Generate one source-bound speaker field and assemble a chair brief on each receipt."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_fresh_briefs as prior

HERE = prior.HERE
runner = prior.runner
FAMILY = "facilitator-bound-fields"
CAP = 43
TASK = (
    "Write one short sentence stating this speaker's documentary position on the issue in the proposed joint "
    "statement. Read only the supplied source. Preserve the actor and the decisive condition, objection or limitation. "
    "If the source has no relevant position, say that the speaker's position is unverified. When wording leaves the "
    "exact assertion unresolved but gives a relevant reservation, state the reservation. Distinguish hope for future "
    "authorization from an adopted authorization or an unconditional call. Do not use source IDs or write a heading. "
    "Use at most 21 words and one sentence."
)


def requests():
    for family, i in prior.PANELS:
        proposal, _, _ = prior.transfer.PANELS[family][i]
        for slot, (speaker, source) in enumerate(prior.transfer.packets()[family]):
            body = {"speaker": speaker, "proposed_joint_statement": proposal, "source": source}
            yield {"id": f"{family}-{i}/S{slot+1}", "cap": CAP, "messages": [
                {"role": "system", "content": TASK},
                {"role": "user", "content": json.dumps(body, ensure_ascii=False)},
            ]}


def episode(generate):
    final = generate(list(requests()))
    return [{"family": FAMILY, "final": final}]


def pins():
    path = Path(__file__).resolve()
    return prior.pins() | {str(path.relative_to(HERE.parents[1])): sha256(path.read_bytes()).hexdigest()}


def read(directory):
    with patch.multiple(prior, pins=pins, requests=requests, CAP=CAP, FAMILY=FAMILY):
        return prior.rows(directory)


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
