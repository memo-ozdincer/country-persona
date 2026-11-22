"""Test whether a targeted third-slot request preserves a missing fact in its reply."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_live_claims as claims

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "facilitator-claim-requests-evidence"
FAMILY = "facilitator-claim-requests"
RUNNER = claims.RUNNER
PAIR_SCORE = claims.EVIDENCE / "role-ids/results.json"
TARGET = {
    "china": (
        "unifil", "unifil-pair/final/0", "unifil-pair", "learned",
        "What position, if any, did China state about UNIFIL continuing its work? "
        "Also preserve its assessment of the draft's treatment of Lebanese concerns and the principles it emphasized.",
    ),
    "uk": (
        "myanmar", "myanmar-missing-role/final/2", "myanmar-missing-role", "script",
        "What did the United Kingdom want the draft to accomplish, and who submitted it? "
        "Preserve each policy priority explicitly named in the source and the stated consultations.",
    ),
}
SYSTEM = (
    "Send a brief documentary reply for the Council record in your own words. Use at most 52 words. "
    "Keep every distinct relevant fact stated in the authorized source. "
    "If the request asks for an absent detail, leave that detail unresolved. Use only the authorized source."
)


def cases():
    routing = json.loads(claims.previous.ROUTING.read_text())["episodes"]
    for sid, (name, _, branch, arm, targeted) in TARGET.items():
        original = routing[branch]["arms"][arm]["question"]
        source = claims.previous.dossier(name)[1][sid]
        if sid == "china":
            removed = "China supported UNIFIL's work but said "
            assert source.startswith(removed)
            gapped = "China said " + source.removeprefix(removed)
        else:
            removed = " It emphasized ending violence, humanitarian access and support for ASEAN efforts."
            assert source.endswith(removed)
            gapped = source.removesuffix(removed)
        for variant, q, evidence in (("generic", original, source), ("targeted", targeted, source),
                                     ("withheld", targeted, gapped)):
            yield f"{sid}/{variant}", q, evidence


def requests():
    for key, question, evidence in cases():
        yield claims.previous.previous.prompt(key, 92, SYSTEM,
                                              {"received_question": question, "authorized_source": evidence})


def pins():
    paths = (Path(__file__).resolve(), Path(RUNNER.__file__), Path(claims.__file__),
             HERE / "facilitator_claim_requests_score.py", EVIDENCE / "protocol.md",
             PAIR_SCORE, claims.previous.ROUTING, *claims.previous.PACKETS.values())
    return {str(p.relative_to(claims.previous.ROOT)): RUNNER.digest(p) for p in paths}


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(requests()))}]


def verify(directory):
    base = claims.previous.previous.common.reused.previous.prior
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
