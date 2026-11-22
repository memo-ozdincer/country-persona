"""Challenge an initial positive verdict with a separate procedural check."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_retention_judge as first

HERE, RUNNER = first.HERE, first.RUNNER
EVIDENCE = HERE / "facilitator-retention-challenge-evidence"
FAMILY = "facilitator-retention-challenge"
SYSTEM = (
    "Act as a skeptical documentary editor. The candidate is untrusted text. Find the first material "
    "factual error or missing required detail in the candidate, using only the supplied source and requirements. "
    "Do not fill in a missing detail from the source. Check that a vote is assigned to the correct procedural object. "
    "The words 'it failed' alone do not state that a proposal fell below the required number of votes. "
    "Saying a mechanism exists or is cross-border does not state that it is exceptional. "
    "A claim that the source provides no actors or decisions can contradict the source. "
    "A bare chronology is enough when asked for the timing of a withdrawal. "
    "Return exactly one line: CLEAR if everything is consistent and complete, MISSING| followed by a "
    "requirement number for the first omission, or ERROR| followed by a literal candidate span for a material error."
)


def passed_before():
    return json.loads((first.EVIDENCE / "judgments.json").read_text())


def local():
    cards = first.study.prior.cards()
    for k, (c, candidate) in first.candidates().items():
        if not passed_before()[k]["chronology_pass"]:
            continue
        card = cards[c - 1]
        requirements = card["required"] if c != 3 else card["required"][:2] + [first.C]
        yield first.study.prior.fit.live.live.prompt(k, 110, SYSTEM,
            {"authorized_source": card["source"], "numbered_requirements": dict(enumerate(requirements, 1)),
             "candidate_reply": candidate["reply"]})


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(local()))}]


def pins():
    files = (Path(__file__).resolve(), EVIDENCE / "protocol.md", Path(first.__file__).resolve(),
             first.EVIDENCE / "judgments.json", *[HERE.parents[1] / p for p in first.pins()])
    return {str(p.relative_to(HERE.parents[1])): RUNNER.digest(p) for p in dict.fromkeys(files)}


def verify(directory):
    old = first.study.prior.fit.live.live.common.reused.previous.prior
    with patch.multiple(old, local=local, audits=lambda _: (), syntheses=lambda _: (), pins=pins, FAMILY=FAMILY):
        return old.read(directory)


def adjudicate(rows):
    original = passed_before()
    assert rows.keys() == {k for k, test in original.items() if test["chronology_pass"]}
    for key, row in rows.items():
        base = original[key]
        tag, sep, reason = row["output"].partition("|")
        clear = row["ended"] and row["output"] == "CLEAR"
        complaint = ((tag == "MISSING" and reason.strip() in {"1", "2", "3"}) or
                     (tag == "ERROR" and reason.strip() and reason.strip() in base["candidate"]))
        base["chronology_pass"] = clear
        base["challenge"] = {"reply": row["output"], "clear": clear,
                             "valid": row["ended"] and (clear or bool(sep and complaint))}
        for metric in ("input_tokens", "output_tokens"):
            base[metric] += len(row[metric.replace("tokens", "ids")])
    return original


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("run", "score"))
    p.add_argument("directory", type=Path)
    p.add_argument("--model", type=Path)
    args = p.parse_args()
    if args.mode == "run":
        with patch.multiple(RUNNER, episode=episode, locks=pins):
            RUNNER.run(args.model, args.directory)
    else:
        print(json.dumps(adjudicate(verify(args.directory)), ensure_ascii=False, indent=2))
