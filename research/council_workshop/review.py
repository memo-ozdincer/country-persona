"""Export a blind clause review and replay its quote-grounded score."""

import argparse
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

from replay import replay


HERE = Path(__file__).resolve().parent
VALIDATOR = HERE.parent / "unsc-marl-20261119/benchmark-v1.7/judge_score.py"
module = spec_from_file_location("workshop_final_judge_v17", VALIDATOR)
judge = module_from_spec(module)
module.loader.exec_module(judge)


def read(path):
    return json.loads(path.read_text())


def digest(data):
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(canonical.encode()).hexdigest()


def packet(settings, result, rubric):
    case = settings["case"]
    if settings["mode"] != "meeting" or digest(case) != rubric["case_sha256"]:
        raise ValueError("The review rubric must match the completed meeting case")
    if sorted(settings["countries"]) != sorted(rubric["countries"]):
        raise ValueError("The review rubric must match the meeting roster")

    evidence = [{"id": "task", "text": case["brief"]}]
    for country in sorted(settings["countries"]):
        evidence.extend({"id": f"{country}-{i}", "text": text}
                        for i, text in enumerate(case["delegations"][country], 1))
    available = {row["id"] for row in evidence}
    for row in rubric["criteria"]:
        if not row["source_blocks"] or not set(row["source_blocks"]) <= available:
            raise ValueError(f"Invalid evidence scope for {row['id']}")
    content = {
        "mode": "FINAL",
        "task": case["brief"],
        "evidence": evidence,
        "rubric": [row | {"category": "final"} for row in rubric["criteria"]],
        "answer": result["draft"],
    }
    return {"id": f"clause-{digest(content)[:16]}", **content}


def report(packet, verdict, result):
    if packet["answer"] != result["draft"]:
        raise ValueError("Reviewed clause differs from the final meeting draft")
    grades = judge.score(packet, verdict)
    approved = {row["id"]: set(row["source_blocks"]) for row in packet["rubric"]}
    for row in verdict["units"]:
        if any(item["block"] not in approved[row["id"]] for item in row["source"]):
            raise ValueError(f"Evidence outside the allowed scope for {row['id']}")
    return {
        "packet": packet["id"],
        "clause_sha256": sha256(packet["answer"].encode()).hexdigest(),
        "draft_version": result["version"],
        "meeting_outcome": result["status"],
        "advisory_ballots": {country: ballot["vote"] for country, ballot in result["ballots"].items()},
        "semantic_points": grades["final"],
        "guard": grades["guard"],
        "released_points": grades["final"]["lower"] if grades["guard"] == "clear" else 0,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="A completed workshop run")
    parser.add_argument("--rubric", type=Path, default=HERE / "climate-review.json")
    parser.add_argument("--verdict", type=Path, help="Score a verdict against the exact reviewed clause")
    args = parser.parse_args()
    result = replay(args.directory)
    request = packet(read(args.directory / "settings.json"), result, read(args.rubric))
    data = report(request, read(args.verdict), result) if args.verdict else {
        "system": (HERE / "clause-judge.md").read_text(),
        "user": request,
    }
    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
