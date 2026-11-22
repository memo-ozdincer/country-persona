"""Score the protected assembly with the frozen final-record evaluator."""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
RELEASE = HERE.parents[3] / "benchmark-v1.5"
sys.path.insert(0, str(RELEASE))
import evaluate as benchmark


def read(path):
    return json.loads(path.read_text())


def requests(deck):
    return sorted((row["packet"] for row in deck.values()), key=lambda p: p["id"])


def score(deck):
    marks = read(HERE / "marks.json")
    earlier = read(HERE.parent / "scores.json")["scores"]
    cases = benchmark.cases()
    out = {}
    for key, row in deck.items():
        case_id, count, arm = key.split("/")
        case = cases[case_id]
        # Only the last slot is populated. This is a writer crossover.
        response = row["response"]
        inputs = [{}, {}, response]
        canonical = benchmark.final_packet(case, inputs)
        assert {k: v for k, v in row["packet"].items() if k != "id"} == {
            k: v for k, v in canonical.items() if k != "id"
        }
        judgment = {**marks[row["packet"]["id"]], "id": canonical["id"]}
        final = benchmark.final_score(case, inputs, judgment)
        assert final["words"] <= case["word_cap"] if row["body_words"] <= row["body_word_cap"] else (
            "final_word_cap" in final["release_blockers"]
        )
        out.setdefault(case_id, {}).setdefault(count, {})[arm] = final | {
            "input_tokens": response["input_tokens"], "output_tokens": response["output_tokens"]
        }
    assert set(marks) == {row["packet"]["id"] for row in deck.values()}
    totals = {}
    for arm in ("free", "scoped", "literal"):
        totals[arm] = {}
        for count in ("1", "2"):
            rows = [(prior[count] if arm == "free" else out[key][count][arm]) for key, prior in earlier.items()]
            totals[arm][count] = {
                "raw_bounds": [sum(row["raw_70"][i] for row in rows) for i in range(2)],
                "released_points": sum(row["released_70"] for row in rows),
                "released_records": sum(row["release"] for row in rows),
                "strict": sum(row["strict"] for row in rows),
                "correct_mechanical": sum(row["mechanical"]["accepted"] for row in rows),
            }
    return dict(totals=totals, scores=out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("judge-deck", "score"))
    mode = parser.parse_args().mode
    deck = read(HERE / "deck.json")
    benchmark.emit(requests(deck) if mode == "judge-deck" else score(deck))
