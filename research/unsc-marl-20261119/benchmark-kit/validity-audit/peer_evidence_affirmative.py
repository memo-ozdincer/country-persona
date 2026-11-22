"""Test an affirmative wording change and a fixed UNIFIL scope control."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import peer_evidence_factored as factored
from peer_evidence_judge import EVIDENCE, ROOT, read, runner

BASE = EVIDENCE / "peer-evidence-factored"
UNIFIL = ROOT / "crossbench/unifil-record.json"
NEW_QUESTION = "Is this exact claim fully supported by the evidence excerpt?"
QUESTIONS = (factored.QUESTIONS[0], NEW_QUESTION)


def unifil():
    sources = {row["id"]: row["text"] for row in read(UNIFIL)["evidence"]}
    claim = "Brazil said the French text addressed some of Lebanon's concerns."
    bad = claim.replace("some of", "all of")
    note = "Brazil's assessment was that the French draft addressed a portion of Lebanon's concerns."
    distractor = sources["china"]
    official = sources["brazil"]
    return {
        "dossier-only": ("already_visible", claim, official, official, distractor),
        "dossier-and-peer": ("already_visible", claim, official, official, note),
        "new-peer": ("new_peer_evidence", claim, official, distractor, note),
        "unsent-peer": ("not_received", claim, official, distractor, distractor),
        "false-peer": ("unsupported", bad, official, distractor, bad),
    }


def make_request(identifier, claim, excerpt, question, cap=4):
    payload = {"claim": claim, "evidence": excerpt, "question": question}
    return {"id": identifier, "cap": cap, "messages": [
        {"role": "system", "content": factored.SYSTEM},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]}


def deck():
    existing, _ = factored.deck()
    plans = []
    for old in existing[::2]:
        assert old["id"].endswith("/0")
        payload = json.loads(old["messages"][1]["content"])
        assert payload["question"] == QUESTIONS[0]
        plans.append(make_request(old["id"].removesuffix("/0") + "/reword",
                                  payload["claim"], payload["evidence"], NEW_QUESTION))
    pairs, mapping = {}, {}
    for name, (_, claim, *excerpts) in unifil().items():
        identifiers = []
        for excerpt in excerpts:
            pair = (claim, excerpt)
            if pair not in pairs:
                ids = [f"unifil-{len(pairs):02d}/{index}" for index in range(len(QUESTIONS))]
                plans.extend(make_request(id_, claim, excerpt, question)
                             for id_, question in zip(ids, QUESTIONS, strict=True))
                pairs[pair] = ids
            identifiers.append(pairs[pair])
        mapping[name] = identifiers
    return plans, mapping


def episode(generate):
    plans, _ = deck()
    results = {}
    for start in range(0, len(plans), 12):
        results.update(generate(plans[start:start + 12]))
    return [{"family": "peer-evidence-affirmative", "final": results}]


def locks():
    return {**factored.locks(), Path(__file__).name: runner.digest(Path(__file__)),
            UNIFIL.name: runner.digest(UNIFIL),
            "factored/transcript.jsonl": runner.digest(BASE / "transcript.jsonl")}


def score(directory):
    trace = directory / "transcript.jsonl"
    complete = read(directory / "complete.json")
    assert read(directory / "launch.json")["sha256"] == locks()
    assert runner.digest(trace) == complete["transcript_sha256"]
    assert runner.digest(directory / "final-records.json") == complete["final_records_sha256"]
    plans, new_mapping = deck()
    _, old_mapping = factored.deck()
    observed = {}
    for row, plan in zip(map(json.loads, trace.read_text().splitlines()), plans, strict=True):
        assert all(row[key] == value for key, value in plan.items())
        observed[row["id"]] = row["output"]
    assert len(observed) == complete["records"] == len(plans)
    original = factored.score(BASE)
    old = {row["id"]: row["output"] for row in map(json.loads, (BASE / "transcript.jsonl").read_text().splitlines())}
    cases = []
    for row in original["items"]:
        family, name = row["family"], row["condition"]
        ids = [pair[0] for pair in old_mapping[family, name]]
        raw = [[old[key], observed[key.removesuffix("/0") + "/reword"]] for key in ids]
        cases.append(item(family, name, row["expected"], raw))
    for name, (truth, *_) in unifil().items():
        raw = [[observed[key] for key in pair] for pair in new_mapping[name]]
        cases.append(item("unifil", name, truth, raw))
    return {
        "scope": "Two affirmative questions, with a development rewording and a UNIFIL extension absent "
                 "from that development panel. Items are matched claim-level controls from exposed project dockets.",
        "calls_new": len(observed), "calls_reused": 17, "cases": cases,
        "groups": {
            name: summarize([row for row in cases if (row["family"] == "unifil") == is_new])
            for name, is_new in (("development", False), ("unifil_extension", True))
        },
    }


def item(family, condition, expected, raw):
    votes = [[factored.normalized(response, 0) for response in pair] for pair in raw]
    verdicts = [factored.classify(*(pair[index] for pair in votes)) for index in range(len(QUESTIONS))]
    consensus = factored.classify(*(first if first == second else None for first, second in votes))
    assert consensus is None or verdicts == [consensus, consensus]
    return {"family": family, "condition": condition, "expected": expected, "raw": raw,
            "verdicts": verdicts, "consensus": consensus}


def summarize(rows):
    return {
        "cases": len(rows),
        "correct_each_question": [sum(row["verdicts"][i] == row["expected"] for row in rows) for i in range(2)],
        "correct_consensus": sum(row["consensus"] == row["expected"] for row in rows),
        "wrong_consensus": sum(row["consensus"] not in (None, row["expected"]) for row in rows),
        "unresolved": sum(row["consensus"] is None for row in rows),
        "false_peer_credit": [f'{row["family"]}/{row["condition"]}' for row in rows
                              if row["expected"] != "new_peer_evidence" and "new_peer_evidence" in row["verdicts"]],
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "score"))
    cli.add_argument("directory", type=Path, nargs="?")
    args = cli.parse_args()
    if args.mode == "check":
        plans, mapping = deck()
        assert len(plans) == len({p["id"] for p in plans}) == 29
        assert len(mapping) == 5
        print(json.dumps({"new_calls": len(plans), "unifil_cases": len(mapping)}, indent=2))
    elif args.mode == "run":
        model = Path(read(BASE / "launch.json")["model"])
        with patch.object(runner, "episode", episode), patch.object(runner, "locks", locks):
            runner.run(model, args.directory)
    else:
        print(json.dumps(score(args.directory), indent=2))
