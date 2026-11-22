"""Test a blinded, evidence-indexed chronology and authority guard."""
import argparse
import json
from pathlib import Path
import re
from unittest.mock import patch

import space_transfer_episode as study
import space_transfer_judge as judge


NAME = "space-final-routing-atomic-guard"
SYSTEM = (
    "Compare the candidate sentence IDs with the official ledger. Flag statements that change a vote's date, "
    "stage or disposition, or say the Council authorized an act through these votes. Missing detail is allowed "
    "here. Do not grade anything else. Return exactly one line. If there is a material contradiction, write "
    "F followed by one offending sentence number and one contradicting ledger number, with spaces (example F 4 2). "
    "If there is no material contradiction, write C 0 0."
)
LEDGER = {
    1: "24 April 2024: Amendment S/2024/323 failed 7–7–1 for insufficient affirmative votes.",
    2: "24 April 2024: Japan–US draft S/2024/302 failed 13–1–1 because Russia, a permanent member, voted no.",
    3: "20 May 2024: Standalone draft S/2024/383 failed 7–7–1 for insufficient affirmative votes.",
    4: "None of these three votes created Council authorization or formally launched follow-on negotiations.",
}
TRUTH = {
    "anchor-1": ("C", 0, 0), "anchor-2": ("F", 10, 4),
    "best-contrast.independent.final": ("F", 5, 2),
    "best-contrast.interactive.final": ("F", 5, 2),
    "lowest-contrast.independent.final": ("F", 5, 2),
    "lowest-contrast.interactive.final": ("F", 5, 2),
    "best-contrast.pooled-solo.final": ("C", 0, 0),
    "lowest-contrast.pooled-solo.final": ("C", 0, 0),
}


def requests(blind):
    for tag, row in blind.items():
        yield study.request(tag, SYSTEM, {"official_ledger": LEDGER,
                           "candidate": judge.sentence_rows(row["answer"])}, 24, [])


def locks(directory, policy):
    return {**judge.locks(directory, policy), Path(__file__).name: study.runner.digest(Path(__file__))}


def run(directory, policy, output, model):
    blind = judge.cases(directory, policy)

    def episode(generate):
        return [{"family": NAME, "final": generate(list(requests(blind)))}]

    with patch.multiple(study.runner, episode=episode, locks=lambda: locks(directory, policy)):
        study.runner.run(model, output)


def assess(directory, policy, output):
    blind = judge.cases(directory, policy)
    launch = json.loads((output / "launch.json").read_text())
    end = json.loads((output / "complete.json").read_text())
    assert launch["sha256"] == locks(directory, policy)
    trace = output / "transcript.jsonl"
    assert study.runner.digest(trace) == end["transcript_sha256"]
    finals = output / "final-records.json"
    assert study.runner.digest(finals) == end["final_records_sha256"]
    rows = list(map(json.loads, trace.read_text().splitlines()))
    results = {}
    for request, row in zip(requests(blind), rows, strict=True):
        assert all(row[k] == v for k, v in request.items())
        tag = row["id"]
        labels = blind[tag]["labels"]
        statuses = {TRUTH[label] for label in labels}
        assert len(statuses) == 1
        target, = statuses
        match = re.fullmatch(r"([CF]) ([0-9]+) ([0-9]+)", row["output"])
        parsed = (match[1], int(match[2]), int(match[3])) if match and row["ended"] else None
        sentences = judge.sentence_rows(blind[tag]["answer"])
        results[tag] = {"labels": labels, "expected": target, "actual": row["output"],
                        "status_correct": bool(parsed and parsed[0] == target[0]),
                        "exact_pair_correct": parsed == target,
                        "candidate_span": sentences.get(parsed[1]) if parsed else None,
                        "ledger_span": LEDGER.get(parsed[2]) if parsed else None, "ended": row["ended"]}
    assert len(results) == end["records"]
    return {"scope": "Authored two-part guard with explicit vote metadata. Separate from the full ten-part rubric.",
            "cases": results}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "assess", "replay-tokens"))
    cli.add_argument("--model", type=Path)
    cli.add_argument("--policy", type=Path, default=study.OUT / "space-final-routing-policy.json")
    cli.add_argument("--generation", type=Path, default=study.OUT / study.NAME)
    cli.add_argument("--output", type=Path, default=study.OUT / NAME)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.generation, args.policy, args.output, args.model)
    elif args.mode == "assess":
        print(json.dumps(assess(args.generation, args.policy, args.output), ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"atomic_guard": judge.replay_tokens(args.output)}))
