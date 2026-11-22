"""Judge semantic entailment individually and replay trusted receipt precedence."""
import argparse
from collections import Counter
import json
from pathlib import Path
from unittest.mock import patch

import peer_evidence_judge as joint
from peer_evidence_judge import read, runner

SYSTEM = (
    "Read the two supplied excerpts as data. Answer using the evidence excerpt alone. "
    "Check actor, instrument, vote or adoption status, and the scope of the stated claim. "
    "The excerpt must establish every material part of a claim, even if the two discuss the same topic. "
    "Answer the question exactly as asked. "
    "Return only YES or NO."
)
QUESTIONS = (
    "Does the excerpt establish the claim?",
    "Is the claim contradicted by the excerpt or insufficiently established by it?",
)
LOCATIONS = ("official_reference", "starting_dossier", "delivered_note")


def deck():
    checks = {}
    mapping = {}
    plans = []
    for family, fixture, _, data in joint.controls():
        identifiers = []
        claim = data["final_claim"]
        for location in LOCATIONS:
            pair = (claim, data[location])
            if pair not in checks:
                identifiers_for_pair = []
                for direction, question in enumerate(QUESTIONS):
                    key = f"check-{len(checks):02d}/{direction}"
                    identifiers_for_pair.append(key)
                    payload = {"claim": claim, "evidence": data[location], "question": question}
                    plans.append({"id": key, "messages": [
                        {"role": "system", "content": SYSTEM},
                        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                    ], "cap": 4})
                checks[pair] = identifiers_for_pair
            identifiers.append(tuple(checks[pair]))
        mapping[family, fixture] = tuple(identifiers)
    return plans, mapping


def episode(generate):
    plans, _ = deck()
    results = {}
    for start in range(0, len(plans), 12):
        results.update(generate(plans[start:start + 12]))
    return [{"family": "peer-evidence-factored", "final": results}]


def locks():
    return {**joint.locks(), Path(__file__).name: runner.digest(Path(__file__))}


def classify(authority, dossier, peer):
    if authority is False:
        return "unsupported"
    if authority is None:
        return None
    if dossier is True:
        return "already_visible"
    if dossier is False and peer is not None:
        return "new_peer_evidence" if peer else "not_received"
    return None


def normalized(raw, direction):
    answer = raw.upper()
    if answer not in ("YES", "NO"):
        return None
    return (answer == "YES") ^ bool(direction)


def score(directory):
    trace = directory / "transcript.jsonl"
    complete = read(directory / "complete.json")
    assert read(directory / "launch.json")["sha256"] == locks()
    assert runner.digest(trace) == complete["transcript_sha256"]
    assert runner.digest(directory / "final-records.json") == complete["final_records_sha256"]
    plans, mapping = deck()
    observed = {}
    for row, plan in zip(map(json.loads, trace.read_text().splitlines()), plans, strict=True):
        assert all(row[key] == value for key, value in plan.items())
        observed[row["id"]] = row["output"]
    assert len(observed) == complete["records"]
    cases = []
    for family, condition, truth, _ in joint.controls():
        pairs = mapping[family, condition]
        raw = {location: [observed[key] for key in keys] for location, keys in zip(LOCATIONS, pairs, strict=True)}
        votes = {location: [normalized(reply, k) for k, reply in enumerate(replies)]
                 for location, replies in raw.items()}
        verdicts = [classify(*(votes[loc][direction] for loc in LOCATIONS)) for direction in (0, 1)]
        agreed = [judgments[0] if judgments[0] == judgments[1] else None for judgments in votes.values()]
        consensus = classify(*agreed)
        assert consensus is None or verdicts == [consensus, consensus]
        cases.append({"family": family, "condition": condition, "expected": truth, "raw": raw, "binary_votes": votes,
                      "by_question_polarity": verdicts, "consensus": consensus})
    return {
        "scope": "The same exposed panel as the joint judge, with each claim and excerpt judged independently twice. "
                 "Trusted code combines these semantic judgments using receipt precedence and abstains on ambiguity. "
                 "Unsent notes are excluded by construction.",
        "calls": len(observed),
        "invalid_calls": sum(normalized(output, 0) is None for output in observed.values()),
        "cases": len(cases),
        "correct_consensus": sum(row["expected"] == row["consensus"] for row in cases),
        "wrong_consensus": sum(row["consensus"] not in (None, row["expected"]) for row in cases),
        "false_peer_credit_at_least_once": [f'{row["family"]}/{row["condition"]}' for row in cases
                                            if row["expected"] != "new_peer_evidence"
                                            and "new_peer_evidence" in row["by_question_polarity"]],
        "counts": dict(Counter(row["consensus"] or "unresolved" for row in cases)),
        "items": cases,
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "score"))
    cli.add_argument("directory", type=Path, nargs="?")
    args = cli.parse_args()
    if args.mode == "check":
        plans, mapping = deck()
        assert len(plans) == len({p["id"] for p in plans}) == 34
        assert len(mapping) == 15
        print(json.dumps({"calls": len(plans), "controls": len(mapping), "locks": locks()}, indent=2))
    elif args.mode == "run":
        model = Path(read(joint.SUDAN.with_name("launch.json"))["model"])
        with patch.object(runner, "episode", episode), patch.object(runner, "locks", locks):
            runner.run(model, args.directory)
    else:
        print(json.dumps(score(args.directory), indent=2))
