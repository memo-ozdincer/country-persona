"""Record UNAMA evidence under all receipt masks, with Council action fixed or written freely."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_requested_evidence as previous

HERE = previous.HERE
EVIDENCE = HERE / "facilitator-unama-authority-evidence"
FAMILY = "facilitator-unama-authority"
runner = previous.prior.runner
CAP = 192
POLICY_ARCHIVE = HERE.parents[1] / "benchmark-kit/evidence/source-request-policy.json"
FIELD_TASK = (
    "Write only the delegate supplement of a Council meeting record. For each delivered source, write one "
    "line beginning with its exact bracketed ID. Preserve all distinct points about what that delegate "
    "supported, wanted or qualified, including the relevant actor, object and restriction. "
    "Use only the delivered statements. Report delegation positions as statements, not decisions. "
    "Keep each line under 34 words. Do not write a heading or a Council decision."
)
RAW_TASK = (
    "Write a Council record of at most 145 words. State the outcome and precise roll call, the Council's "
    "decision about the mandate including its end date, and its separate reporting request including its "
    "interval and recipient. Describe the positions and qualifications of any delegations with evidence "
    "delivered. Cite each source by its bracketed ID and preserve which institution acted or spoke. "
    "Use only the delivered sources."
)


def packet():
    return json.loads((EVIDENCE / "packet.json").read_text())


def selected(mask, source):
    return {sid: field["passage"] for i, (sid, field) in enumerate(source["cards"].items()) if mask & (1 << i)}


def requests():
    source = packet()
    for mask in range(1, 8):
        yield previous.prior.prompt(f"bound/{mask}", CAP, FIELD_TASK, {"delivered": selected(mask, source)})
    for mask in (0, 7):
        evidence = source["public"] | selected(mask, source)
        yield previous.prior.prompt(f"raw/{mask}", CAP, RAW_TASK, {"delivered": evidence})


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(requests()))}]


def pins():
    files = (Path(__file__).resolve(), Path(runner.__file__), EVIDENCE / "packet.json",
             EVIDENCE / "rubric.md", EVIDENCE / "provenance.json", POLICY_ARCHIVE)
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
