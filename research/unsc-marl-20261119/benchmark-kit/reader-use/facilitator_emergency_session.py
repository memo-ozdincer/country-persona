"""Generate the frozen emergency-session transfer benchmark."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_unama_authority as reused

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "facilitator-emergency-session-evidence"
FIT = HERE / "facilitator-guard-calibrated-fit-evidence/fit.json"
FAMILY = "facilitator-emergency-session"
CAP = reused.CAP
RAW = (
    "Write a Council record of at most 145 words. Report the outcome and precise roll call. "
    "Describe the exact procedural decision and the role of the earlier Council meeting. "
    "Preserve the positions and qualifications of the delegations you have evidence for. "
    "Cite each source by its bracketed ID and distinguish Council decisions from delegation statements. "
    "Use only the delivered sources."
)


def packet():
    return json.loads((EVIDENCE / "packet.json").read_text())


def requests():
    source = packet()
    make = reused.previous.prior.prompt
    for mask in range(1, 8):
        yield make(f"bound/{mask}", CAP, reused.FIELD_TASK, {"delivered": reused.selected(mask, source)})
    for mask in (0, 7):
        yield make(f"raw/{mask}", CAP, RAW, {"delivered": source["public"] | reused.selected(mask, source)})


def pins():
    files = (Path(__file__).resolve(), Path(reused.__file__), Path(reused.runner.__file__), FIT,
             HERE / "facilitator_emergency_session_score.py", HERE / "facilitator_guard_calibrated_fit.py",
             HERE / "facilitator_unama_authority_score.py",
             EVIDENCE / "packet.json", EVIDENCE / "protocol.md", EVIDENCE / "provenance.json")
    return {str(path.relative_to(HERE.parents[1])): reused.runner.digest(path) for path in files}


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(requests()))}]


def verify(directory):
    base = reused.previous.prior
    with patch.multiple(base, local=requests, audits=lambda rows: (), syntheses=lambda rows: (),
                        pins=pins, FAMILY=FAMILY):
        return base.read(directory)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("run", "verify"))
    p.add_argument("directory", type=Path)
    p.add_argument("--model", type=Path)
    args = p.parse_args()
    if args.mode == "verify":
        print(json.dumps({"verified_generations": len(verify(args.directory))}))
    else:
        with patch.multiple(reused.runner, episode=episode, locks=pins):
            reused.runner.run(args.model, args.directory)
