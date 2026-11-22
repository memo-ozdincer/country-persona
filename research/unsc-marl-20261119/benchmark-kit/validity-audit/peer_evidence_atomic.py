"""Separate archived final claims into atoms and test source coverage and paraphrase."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import peer_evidence_affirmative as affirmative
import peer_evidence_judge as joint
from peer_evidence_judge import read, runner

EARLIER = joint.EVIDENCE / "peer-evidence-affirmative/scores.json"


def cases():
    anchors = joint.anchors()
    outer = anchors["outer-space"]
    sudan = anchors["sudan"]
    blocks = {row["id"]: row["text"] for row in read(joint.SOURCE_FILES[1])["evidence"]}
    vote = blocks["apr-amendment"]
    reason = blocks["china-reason"]
    later = blocks["apr-final"]
    combined = vote + "\n" + reason
    vote_claim = "China supported amendment S/2024/323 to the April draft."
    reason_claim = "Through the April amendment, China sought early work toward binding multilateral agreements."
    no_vote = "China supported the final April draft S/2024/302."
    access = "The Sudan draft proposed facilitating humanitarian access."
    deny_access = "The Sudan draft proposed blocking humanitarian access."
    generic = "The draft discussed the humanitarian situation and civilian protection."
    receipt = {
        "old_wording": sudan["note"],
        "short_paraphrase": "One aim of the Sudan draft was to let humanitarian aid reach people.",
        "wrong_direction": "One aim of the Sudan draft was to stop humanitarian aid from reaching people.",
    }
    return [
        ("space-combined/peer-visible", "new_peer_evidence", outer["claim"], combined, vote, outer["note"]),
        ("space-vote/peer-visible", "already_visible", vote_claim, vote, vote, outer["note"]),
        ("space-vote/repeated", "already_visible", vote_claim, vote, vote, vote),
        ("space-vote/wrong-instrument", "unsupported", no_vote, later, vote, no_vote),
        ("space-reason/peer-visible", "new_peer_evidence", reason_claim, reason, vote, outer["note"]),
        ("space-reason/unsent", "not_received", reason_claim, reason, vote, outer["distractor"]),
        ("space-reason/pre-shared", "already_visible", reason_claim, reason, combined, outer["note"]),
        ("sudan-access/old-note", "new_peer_evidence", access, sudan["reference"], sudan["distractor"], receipt["old_wording"]),
        ("sudan-access/short-paraphrase", "new_peer_evidence", access, sudan["reference"], generic, receipt["short_paraphrase"]),
        ("sudan-access/near-miss", "not_received", access, sudan["reference"], sudan["distractor"], generic),
        ("sudan-access/wrong-direction", "unsupported", deny_access, sudan["reference"], generic, receipt["wrong_direction"]),
    ]


def deck():
    pairs, plans, mapping = {}, [], {}
    for name, _, claim, *excerpts in cases():
        mapping[name] = []
        for excerpt in excerpts:
            key = (claim, excerpt)
            if key not in pairs:
                ids = [f"pair-{len(pairs):02d}/{i}" for i in range(2)]
                plans.extend(affirmative.make_request(id_, claim, excerpt, question)
                             for id_, question in zip(ids, affirmative.QUESTIONS, strict=True))
                pairs[key] = ids
            mapping[name].append(pairs[key])
    return plans, mapping


def episode(generate):
    plans, _ = deck()
    results = {}
    for start in range(0, len(plans), 12):
        results.update(generate(plans[start:start + 12]))
    return [{"family": "peer-evidence-atomic", "final": results}]


def locks():
    return {**affirmative.locks(), "affirmative_script": runner.digest(Path(affirmative.__file__)),
            "earlier_score": runner.digest(EARLIER), "atomic_script": runner.digest(Path(__file__))}


def score(directory):
    trace = directory / "transcript.jsonl"
    complete = read(directory / "complete.json")
    assert read(directory / "launch.json")["sha256"] == locks()
    assert runner.digest(trace) == complete["transcript_sha256"]
    finals = directory / "final-records.json"
    assert runner.digest(finals) == complete["final_records_sha256"]
    plans, mapping = deck()
    responses = {}
    for row, plan in zip(map(json.loads, trace.read_text().splitlines()), plans, strict=True):
        assert all(row[key] == value for key, value in plan.items())
        responses[row["id"]] = row["output"]
    assert len(responses) == len(plans) == complete["records"]
    assert read(finals)["peer-evidence-atomic"] == responses
    items = []
    for name, expected, *_ in cases():
        family, condition = name.split("/", 1)
        raw = [[responses[key] for key in pair] for pair in mapping[name]]
        items.append(affirmative.item(family, condition, expected, raw))
    return {
        "scope": "The same frozen judge and affirmative questions on exposed historical controls. "
                 "Candidate facts are preselected and the follow-up changes excerpt completeness and claim scope.",
        "calls": len(responses), "summary": affirmative.summarize(items),
        "subsets": {k: affirmative.summarize([r for r in items if r["family"] == k]) for k in
                    ("space-combined", "space-vote", "space-reason", "sudan-access")},
        "items": items,
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "score"))
    cli.add_argument("directory", type=Path, nargs="?")
    args = cli.parse_args()
    if args.mode == "check":
        plans, mapping = deck()
        print(json.dumps({"calls": len(plans), "controls": len(mapping), "locks": locks()}, indent=2))
    elif args.mode == "run":
        model = Path(read(affirmative.BASE / "launch.json")["model"])
        with patch.object(runner, "episode", episode), patch.object(runner, "locks", locks):
            runner.run(model, args.directory)
    else:
        print(json.dumps(score(args.directory), indent=2))
