"""Generate one bounded source-local note per card in two exposed dockets."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_emergency_session as emergency
import facilitator_unama_authority as unama

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "facilitator-modular-record-evidence"
FAMILY = "facilitator-modular-record"
CAP = 68
WORDS = 27
TASK = (
    "Write one compact predicate for a Council record after the supplied speaker prefix. Start with a verb, "
    "omit the subject name and citations, and use at most 27 words. Preserve distinct supported positions "
    "and qualifications from the single source. Use precise verbs and entities. Return only the predicate "
    "on one line."
)
UNAMA_PUBLIC = {
    "S0": "On 17 March 2022 the Council adopted resolution 2626 (2022), 14 in favour, none against and one abstention by Russia.",
    "S1": "The Council decided to extend the UNAMA mandate until 17 March 2023 and requested that the Secretary-General report to the Council every three months on Afghanistan and mandate implementation.",
}


def cases():
    # Recover the settled text from the earlier compacted arm.
    compact = json.loads((emergency.EVIDENCE / "compact.json").read_text())
    session = emergency.packet()
    names = {"S2": "Brazil", "S3": "Nebenzia, speaking for Russia,", "S4": "India"}
    return {
        "unama": {"public": UNAMA_PUBLIC, "cards": unama.packet()["cards"],
                  "speakers": {"S2": "Norway", "S3": "Russia", "S4": "China"}},
        "emergency": {"public": compact["sources"], "cards": session["cards"], "speakers": names},
    }


def requests():
    for name, source in cases().items():
        for sid, card in source["cards"].items():
            yield unama.previous.prior.prompt(f"{name}/{sid}", CAP, TASK, {
                "speaker_prefix": source["speakers"][sid], "source": card["passage"],
            })


def pins():
    files = (Path(__file__).resolve(), Path(unama.runner.__file__),
             HERE / "facilitator_modular_record_score.py", EVIDENCE / "protocol.md",
             unama.EVIDENCE / "packet.json", unama.EVIDENCE / "results.json",
             emergency.EVIDENCE / "packet.json", emergency.EVIDENCE / "compact.json",
             emergency.FIT, HERE / "facilitator_emergency_session_score.py")
    return {str(path.relative_to(HERE.parents[1])): unama.runner.digest(path) for path in files}


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(requests()))}]


def verify(directory):
    base = unama.previous.prior
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
        with patch.multiple(unama.runner, episode=episode, locks=pins):
            unama.runner.run(args.model, args.directory)
