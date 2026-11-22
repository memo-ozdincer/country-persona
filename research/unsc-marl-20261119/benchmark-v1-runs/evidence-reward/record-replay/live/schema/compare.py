"""Compare raw schema adherence and a local typed-card extraction control."""
import argparse
import json
from pathlib import Path
import re

import clarify
import score as review

HERE = Path(__file__).resolve().parent
r = clarify.live.r


def deterministic(request):
    payload = json.loads(request["messages"][1]["content"])
    prefix = re.escape(payload["role"]) + r" fictional constraint: "
    matched = re.fullmatch(prefix + r"([a-z_]+) = ([a-z_]+)\.", payload["own_card"])
    if matched is None:
        raise ValueError("Card is outside the registered typed form")
    field, value = matched.groups()
    return {"text": json.dumps({"field": field, "value": value}),
            "input_tokens": 0, "output_tokens": 0, "termination": "complete"}


def baseline():
    originals = r.e.read(HERE.parent / "requests.json")
    result = review.score([{**row, "response": deterministic(row["request"])} for row in originals])
    result["scope"] = "deterministic role-local extraction on the registered typed card"
    return result


def compare():
    initial = r.e.read(HERE.parent / "results.json")
    explicit = review.score(review.rows(HERE / "evidence/records.jsonl"))
    explicit["scope"] = "four schema-clarified Qwen follow-ups in the same reconstructed states"
    simple = baseline()
    assert initial["expected_proof"] == explicit["expected_proof"] == simple["expected_proof"]
    reduced = lambda item: {k: v for k, v in item.items() if k != "results"}
    return {"initial": reduced(initial), "clarified": explicit, "deterministic": simple}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("verify", "baseline", "score"))
    mode = parser.parse_args().mode
    if mode == "verify":
        result = review.inspect(HERE / "evidence", clarify.pins(), clarify.requests())
    else:
        result = baseline() if mode == "baseline" else compare()
    r.e.emit(result)
