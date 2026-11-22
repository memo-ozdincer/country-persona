"""Apply the frozen final rubric to the paired writer crossover."""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
RELEASE = HERE.parents[2] / "benchmark-v1.5"
sys.path.insert(0, str(RELEASE))
import evaluate as benchmark


def load(name):
    return json.loads((HERE / name).read_text())


def judge_deck(deck):
    packs = [row["packet"] for row in deck.values()]
    cases = benchmark.cases()
    for case_route, row in deck.items():
        key, _ = case_route.split("/")
        packet = benchmark.final_packet(cases[key], [{}, {}, row["response"]])
        # The collector uses a shorter opaque ID. Validate all substantive fields.
        assert {k: v for k, v in packet.items() if k != "id"} == {
            k: v for k, v in row["packet"].items() if k != "id"
        }
    return sorted(packs, key=lambda packet: packet["id"])


def score(deck, marks):
    cases = benchmark.cases()
    packets = judge_deck(deck)
    assert {p["id"] for p in packets} == set(marks)
    scores = {}
    for key, row in deck.items():
        case, report_count = key.split("/")
        candidate = row["response"]
        slots = [{}, {}, candidate]  # Final-only crossover. There are no generated notes.
        packet = benchmark.final_packet(cases[case], slots)
        old_id = row["packet"]["id"]
        grade = dict(marks[old_id], id=packet["id"])
        result = benchmark.final_score(cases[case], slots, grade)
        scores.setdefault(case, {})[report_count] = result | {
            "input_tokens": candidate["input_tokens"], "output_tokens": candidate["output_tokens"]
        }
    paired = {key: dict(released_delta=units["2"]["released_70"] - units["1"]["released_70"],
                        raw_lower_delta=units["2"]["raw_70"][0] - units["1"]["raw_70"][0],
                        criterion_changes={unit: (value, units["2"]["units"][unit])
                                           for unit, value in units["1"]["units"].items()
                                           if value != units["2"]["units"][unit]})
              for key, units in scores.items()}
    return dict(scores=scores, paired=paired)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("deck", "score"))
    cmd = parser.parse_args().mode
    raw = load("deck.json")
    benchmark.emit(judge_deck(raw) if cmd == "deck" else score(raw, load("marks.json")))
