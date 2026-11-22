"""Audit the unedited explanation after composing it into the protected memo."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import relay_memo_review as review
import relay_ranked_reason as reason


def deck(directory, scenario=reason.scenario, prompt_cap=35):
    with scenario():
        generation = reason.final.generation
        # Match the shape of JSON records while retaining the locked writer source.
        plans = json.loads(json.dumps(list(generation.suite()), ensure_ascii=False))
        with patch.object(generation, "suite", new=lambda: iter(plans)):
            runs = review.verify(directory)
    cases, joins, composed = {}, {}, {}
    for row in runs:
        ref = sha256(("ranked-reason/" + row["id"]).encode()).hexdigest()[:10]
        prompt = row["expected"]
        response = row["output"]
        frame = prompt["frame"]
        document = "\n\n".join((*frame[:2], response, frame[-1]))
        cases[ref] = {"response": response, "certificate": prompt["certificate"],
                      "word_limit": min(prompt_cap, prompt["word_limit"])}
        joins[ref] = row["id"]
        composed[ref] = {
            "memo": document,
            "words": len(document.split()),
            "reason_words": len(response.split()),
            "body_as_generated": response,
            "exact_heading": document.splitlines()[0] == frame[0],
            "facts_intact": frame[1] in document and document.endswith(frame[-1]),
            "stop": row["stop"],
        }
    return dict(sorted(cases.items())), joins, composed


def measure(folder, annotations, scenario=reason.scenario, prompt_cap=35):
    cases, joins, composed = deck(folder, scenario, prompt_cap)
    marks = annotations["reviews"]
    assert set(cases) == set(marks)
    results = {}
    for ref, row in cases.items():
        mark = marks[ref]
        spans = mark["response_spans"]
        assert spans and all(s and s in row["response"] for s in spans), (ref, spans)
        certificate_spans = mark["certificate_spans"]
        certificate = json.dumps(row["certificate"], sort_keys=True)
        assert certificate_spans and all(s and s in certificate for s in certificate_spans)
        assert isinstance(mark["fact_safe"], bool) and isinstance(mark["complete_reason"], bool)
        assert mark["explanation"]
        memo = composed[ref]
        under_limit = memo["reason_words"] <= row["word_limit"] and memo["words"] <= 120
        exact_frame = memo["exact_heading"] and memo["facts_intact"]
        passed = under_limit and exact_frame and mark["fact_safe"] and mark["complete_reason"] and memo["stop"] == "eos"
        results[joins[ref]] = {**memo, "within_limits": under_limit, **mark, "pass": passed}
    return {"scope": annotations["scope"], "results": results}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    cli.add_argument("--annotations", type=Path)
    cli.add_argument("--short", action="store_true")
    args = cli.parse_args()
    scenario, cap = reason.scenario, 35
    if args.short:
        from relay_ranked_reason_short import scenario
        cap = 32
    if args.annotations:
        print(json.dumps(measure(args.directory, json.loads(args.annotations.read_text()), scenario, cap),
                         indent=2, ensure_ascii=False))
    else:
        cases, _, _ = deck(args.directory, scenario, cap)
        print(json.dumps(cases, indent=2, ensure_ascii=False))
