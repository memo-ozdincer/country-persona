"""Select and evaluate a source-local writing interface using out-of-docket probes."""
import argparse
import json
from pathlib import Path
import re
from unittest.mock import patch

import facilitator_channel_fit as fit

source = fit.live
RUNNER = source.RUNNER
HERE = source.HERE
EVIDENCE = HERE / "facilitator-preflight-2699-evidence"
PACKET = EVIDENCE / "packet.json"
CANARIES = EVIDENCE / "canaries.json"
FAMILY = "facilitator-preflight-2699"


def packet():
    return json.loads(PACKET.read_text())


def canaries():
    return json.loads(CANARIES.read_text())


def probe_requests():
    for i, case in enumerate(canaries(), 1):
        for name, text in (("visible", case["question"]), ("source_only", "")):
            yield source.live.prompt(f"probe/{i}/{name}", 92, source.prior_claims.SYSTEM,
                                     {"received_question": text, "authorized_source": case["source"]})


def local():
    with patch.object(source, "packet", packet):
        return list(source.decode_requests())


def audits(rows):
    with patch.object(source, "packet", packet):
        return [*probe_requests(), *source.reply_requests(rows)]


def episode(generate):
    rows = generate(local())
    pending = audits(rows)
    for start in range(0, len(pending), 6):
        rows.update(generate(pending[start:start + 6]))
    return [{"family": FAMILY, "final": rows}]


def pins():
    files = (Path(__file__).resolve(), PACKET, CANARIES, EVIDENCE / "protocol.md", Path(fit.__file__),
             fit.EVIDENCE / "results.json")
    return {**source.pins(), **{str(p.relative_to(HERE.parents[1])): RUNNER.digest(p) for p in files}}


def verify(directory):
    previous = source.live.common.reused.previous.prior
    with patch.multiple(previous, local=local, audits=audits, syntheses=lambda _: (), pins=pins, FAMILY=FAMILY):
        return previous.read(directory)


def field_present(text, token):
    return re.search(r"(?<!\w)" + re.escape(token) + r"(?!\w)", text, re.I) is not None


def preflight(rows):
    evidence = {}
    for i, case in enumerate(canaries(), 1):
        for modality in ("visible", "source_only"):
            key = f"probe/{i}/{modality}"
            row = rows[key]
            text = row["output"]
            correct = any(field_present(text, name) for name in case["correct_actor"])
            distractor = any(field_present(text, name) for name in case["other_actor"])
            facts = all(field_present(text, item) for item in case["facts"])
            evidence[key] = {"pass": row["ended"] and len(text.split()) <= 52 and correct and not distractor and facts,
                             "correct_actor_present": correct, "other_actor_present": distractor, "facts_present": facts,
                             "input_tokens": len(row["input_ids"]), "output_tokens": len(row["output_ids"])}
    selected = next((mode for mode in ("visible", "source_only")
                     if all(mark["pass"] for key, mark in evidence.items() if key.endswith("/" + mode))),
                    "independent_source_only")
    return {"selected": selected, "calls": len(evidence),
            "input_tokens": sum(e["input_tokens"] for e in evidence.values()),
            "output_tokens": sum(e["output_tokens"] for e in evidence.values()), "tests": evidence}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "verify", "preflight"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        with patch.multiple(RUNNER, episode=episode, locks=pins):
            RUNNER.run(args.model, args.directory)
    elif args.mode == "verify":
        print(json.dumps({"verified_generations": len(verify(args.directory))}))
    else:
        print(json.dumps(preflight(verify(args.directory)), indent=2))
