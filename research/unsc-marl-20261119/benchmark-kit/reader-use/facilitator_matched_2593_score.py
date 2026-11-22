"""Prepare blind review and score exact-span final-record annotations."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import facilitator_matched_2593 as study

EVIDENCE = study.EVIDENCE
RUBRIC = EVIDENCE / "rubric.json"


def load(path):
    return json.loads(path.read_text())


def blind(rows):
    finals = {key: row for key, row in rows.items() if key.endswith("/final")}
    ordered = sorted(finals, key=lambda k: sha256(("2593-record-review/" + k).encode()).hexdigest())
    return {f"R{i + 1}": finals[key] for i, key in enumerate(ordered)}


def review_inputs(rows):
    return {alias: {"ended": row["ended"], "words": len(row["output"].split()), "response": row["output"]}
            for alias, row in blind(rows).items()}


def evaluate(rows, reviews):
    criteria = load(RUBRIC)
    aliases = blind(rows)
    assert aliases.keys() == reviews.keys()
    records = {}
    for alias, row in aliases.items():
        review = reviews[alias]
        assert review.keys() == criteria.keys()
        response = row["output"]
        for key, (rating, witnesses) in review.items():
            statuses = ("clean", "fail", "uncertain") if key == "G" else ("met", "unmet", "uncertain")
            assert rating in statuses and isinstance(witnesses, list)
            assert all(span and span in response for span in witnesses)
            assert witnesses or rating in ("unmet", "clean", "uncertain")
        cases = [review[key][0] for key in criteria if key != "G"]
        lower = cases.count("met") * 7
        upper = lower + cases.count("uncertain") * 7
        within_limit = row["ended"] and len(response.split()) <= 210
        release = within_limit and review["G"][0] == "clean"
        arm = row["id"].split("/")[0]
        trace = [rows[key] for key in study.trace(arm)]
        records[arm] = {"alias": alias, "coverage_lower": lower, "coverage_upper": upper,
                        "release_points": lower if release else 0, "released": release,
                        "strict": release and lower == 70, "within_limit": within_limit,
                        "words": len(response.split()), "calls": len(trace),
                        "total_completion_cap": sum(r["cap"] for r in trace),
                        "input_tokens": sum(len(r["input_ids"]) for r in trace),
                        "output_tokens": sum(len(r["output_ids"]) for r in trace),
                        "peer_messages_to_desk": 2 if arm == "peer" else 0, "criteria": review}
    return records


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("blind", "score"))
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    rows = study.verify(args.directory)
    result = review_inputs(rows) if args.mode == "blind" else evaluate(rows, load(EVIDENCE / "review.json"))
    print(json.dumps(result, ensure_ascii=False, indent=2))
