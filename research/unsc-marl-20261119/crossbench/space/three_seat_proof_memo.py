"""Evaluate chair writing after deterministic decision verification."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import three_seat_memo as previous

HERE = Path(__file__).resolve().parent
FAMILY = "three-seat-verified-proof"
ROOT = HERE / "three-seat-proof-evidence"
runner = previous.runner
game = previous.game
base_requests = previous.requests
base_locks = previous.locks
INSTRUCTION = (
    "Write the workshop decision from the verified decision summary. Copy its certified disposition "
    "exactly as the first line. Then explain in up to 45 words what the verification proves. "
    "A possible winning package is not necessarily a common winner. Impasse means every compatible "
    "world rules out every package. Unresolved means there is no common winning disposition. "
    "Use no grades or preferences beyond those shown here."
)


def requests():
    for row in base_requests():
        system, prompt = row["messages"]
        body = json.loads(prompt["content"])
        compatible = []
        for world in row["possible"]:
            facts = []
            a, b = game.CARDS_A[world[0]], game.CARDS_B[world[1]]
            for name, grades in zip(game.PACKAGES, zip(a, b, game.PUBLIC, strict=True), strict=True):
                facts.append({"package": name, "lowest_grade": min(grades), "total_grade": sum(grades),
                              "feasible": min(grades) > 0})
            compatible.append({"possible_winners": sorted(game.TRUTH[world]), "comparisons": facts})
        body["task"] = INSTRUCTION
        body["verifier"] = {"certified_disposition": row["key"][0], "verified_possible_completions": compatible}
        yield {**row, "messages": [system, {**prompt, "content": json.dumps(body)}]}


def locks():
    return base_locks() | {Path(__file__).name: runner.digest(Path(__file__))}


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(requests()))}]


def run(model, output):
    with patch.multiple(runner, episode=episode, locks=locks):
        runner.run(model, output)


def score(output):
    with patch.multiple(previous, requests=requests, locks=locks, FAMILY=FAMILY):
        findings = previous.score(output)
    findings["scope"] = "Frozen Qwen prose following the mechanically verified disposition with the same receipts. "                         "The joint policy does not supply a different action and interpretation is reviewed separately."
    return findings


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "score"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.model, args.directory)
    else:
        print(json.dumps(score(args.directory), indent=2))
