"""Run the four rubric-selected full-mandate replies on the pinned checkpoint."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
RECORD = HERE.parent
RUNS = RECORD.parents[1]
sys.path.insert(0, str(RECORD))
import replay as r
sys.path.insert(0, str(RUNS / "syria-baseline"))
import collect as collector

SYSTEM = (
    "You are the named delegate in a fictional post-vote workshop. The chair asks for your complete own "
    "requirement to document a decision already certified by the public signs. Use your private card for "
    "your own requirement. Do not infer another delegate's mandate or report a new decision. "
    "Return exactly one JSON object with two string keys, field and value. No prose."
)


def sources():
    data = r.e.read(RECORD / "replay.json")["paths"]["0.8"]
    cases = r.e.cases()
    for key, arms in data.items():
        for path in arms["value"]:
            record = path["record"]
            if record["full_declarations"]:
                (recipient,) = record["full_declarations"]
                case_id = key.split("/")[0]
                case = cases[case_id]
                idx = r.env.ROLES.index(recipient)
                signals = list(record["signed_evidence"])
                assert signals[-1]["id"] == f"complete:{recipient}"
                assert len(signals) == 4
                for signal in signals[:-1]:
                    assert not signal["id"].startswith("complete:")
                yield key, case, idx, signals[:-1], record["decision"], path["id"], path["probability"]


def requests():
    for key, case, idx, signs, proof, final_id, delivered in sources():
        names = dict(zip(r.env.ROLES, case["roles"], strict=True))
        blocks = case["owned"][idx]
        assert len(blocks) == 1
        payload = {
            "role": case["roles"][idx],
            "question": "What is your own complete fictional workshop requirement for the record?",
            "own_card": blocks[0]["text"],
            "menu": next(row["text"] for row in case["public"] if row["id"] == "menu"),
            "public_signs": [{**signal, "role": names[signal["role"]]} for signal in signs],
            "decision_already_certified": proof,
        }
        yield key, {"max_output_tokens": 100, "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ]}


def pins():
    files = (Path(__file__), HERE / "protocol.md", HERE / "requests.json", RECORD / "replay.json",
             RECORD / "reweighted.json", RECORD / "render.py", RECORD / "marks.json", r.e.HERE / "release.json")
    return {str(p.relative_to(r.env.CHAIR.ROOT)): sha256(p.read_bytes()).hexdigest() for p in files}


def collect(generate, directory):
    expected = r.e.read(HERE / "requests.json")
    assert expected == [{"id": key, "request": req} for key, req in requests()]
    for row in expected:
        collector.suite.append(directory / "records.jsonl", {**row, "response": generate(row["request"])})
    (directory / "followup-lock.json").write_text(json.dumps(pins(), indent=2) + "\n")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("deck", "run"))
    args = cli.parse_args()
    if args.mode == "deck":
        r.e.emit([{"id": key, "request": req} for key, req in requests()])
    else:
        roster = {case["id"]: case for _, case, *_ in sources()}
        assert len(roster) == 2
        with patch.object(collector.suite, "collect", collect), patch.object(collector, "roster", return_value=roster):
            collector.run(HERE / "evidence")
