"""Generate source-bound evidence witnesses for the existing live replies."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_live_writing as previous

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "facilitator-live-claims-evidence"
RAW = previous.EVIDENCE
FAMILY = "facilitator-live-claims"
RUNNER = previous.RUNNER
RULES = {
    "unifil": {
        "brazil-reason": ("brazil", "Brazil judged the text preserved UNIFIL's free operation and addressed some Lebanese concerns."),
        "brazil-support": ("brazil", "Brazil supported UNIFIL's continued work."),
        "china-reason": ("china", "China said Lebanese concerns were insufficiently addressed and emphasized sovereignty or consent."),
        "china-support": ("china", "China supported UNIFIL's continued work."),
        "russia-reason": ("russia", "Russia abstained because late changes lost a prior compromise, but still supported UNIFIL's work."),
    },
    "myanmar": {
        "uk": ("uk", "The UK submitted the draft and emphasized ending violence, humanitarian access, and supporting ASEAN efforts."),
        "india": ("india", "India explained its abstention with regional concerns and a preference for quiet constructive diplomacy."),
        "role": ("chair", "The presidency announced adoption and India's later explanation of its abstention was given in its national capacity."),
    },
}
COMMAND = (
    "Check whether this one passage establishes every material detail of the claim. "
    "If it does, copy a single exact contiguous excerpt containing the relevant evidence. "
    "Return only the excerpt without quotation marks. If anything is absent, contradicted, "
    "or attributable to another speaker, return exactly NONE. A related phrase is insufficient."
)


def old_rows():
    return {row["id"]: row for row in map(json.loads, (RAW / "transcript.jsonl").read_text().splitlines())}


def items(rows):
    witnesses = {}
    for vid, name, _, sources, _ in previous.final_views(rows):
        official = previous.dossier(name)[1]
        for claim, (sid, check) in RULES[name].items():
            if sid not in sources:
                continue
            view = sources[sid]
            if "\nFollow-up note: " in view:
                # The original opening source is already available if the
                # same card was transmitted twice. Retest the original.
                view = view.split("\nFollow-up note: ", 1)[0]
                assert view == official[sid]
            key = f"{name}/{claim}/" + sha256(view.encode()).hexdigest()[:12]
            entry = witnesses.setdefault(key, {"claim": check, "source_id": sid, "evidence": view, "views": []})
            entry["views"].append(vid)
    return witnesses


def requests():
    for key, item in items(old_rows()).items():
        yield previous.previous.prompt(key, 74, COMMAND, {k: item[k] for k in ("claim", "source_id", "evidence")})


def episode(generate):
    calls = list(requests())
    rows = {}
    for beginning in range(0, len(calls), 12):
        rows.update(generate(calls[beginning:beginning + 12]))
    return [{"family": FAMILY, "final": rows}]


def pins():
    files = (Path(__file__).resolve(), Path(previous.__file__), Path(RUNNER.__file__),
             HERE / "facilitator_live_claims_score.py", EVIDENCE / "protocol.md", RAW / "launch.json",
             RAW / "complete.json", RAW / "transcript.jsonl", *previous.PACKETS.values())
    return {str(p.relative_to(previous.ROOT)): RUNNER.digest(p) for p in files}


def verify(directory):
    base = previous.previous.common.reused.previous.prior
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
        with patch.multiple(RUNNER, episode=episode, locks=pins):
            RUNNER.run(args.model, args.directory)
