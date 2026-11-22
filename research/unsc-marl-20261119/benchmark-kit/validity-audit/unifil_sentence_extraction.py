"""Select sentence IDs directly from evidence with no precomposed answer choices."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import unifil_span_review as review
import unifil_span_transport as transport

runner, common = transport.runner, transport.common
NAME = "unifil-sentence-extraction"
OUT = common.OUT / NAME
SYSTEM = (
    "Select two sentence IDs from the named owner that together support all requested details. "
    "Some sentences concern a vote but omit its rationale. Ignore other owners. "
    "Do not infer missing details or complete a fragment from general knowledge. "
    "Reply with the two IDs separated by one space, or NONE if fewer than two relevant authorized sentences are available."
)
CONTEXT = {
    "brazil": "Brazil voted in favour of the adopted text.",
    "china": "The vote on the mandate renewal recorded a Chinese abstention.",
    "russia": "The vote on the mandate renewal recorded a Russian abstention.",
    "may": "The Council had previously considered an April text on the same agenda.",
}


def tests():
    for field, original in transport.get_sources().items():
        first, rest = original.split(". ", 1)
        first += "."
        views = {"intact": True, "missing": False}
        if field == "brazil":
            views["misattributed"] = False
        for view, complete in views.items():
            evidence = [(field, first, "first"), (field, CONTEXT[field], "context")]
            if complete:
                evidence += [(field, rest, "second")]
            elif view == "misattributed":
                evidence += [("unnamed reporter", rest, "outside")]
            for order in transport.ORDERS:
                ordered = evidence if order == "forward" else evidence[::-1]
                identifiers = dict(zip("ABC", ordered, strict=False))
                required = {code for code, fields in identifiers.items() if fields[2] == "first"
                            or fields[2] == "second"} if complete else set()
                task = {"owner": field, "details": transport.FIELDS[field]["question"],
                        "sentences": {key: {"owner": row[0], "text": row[1]} for key, row in identifiers.items()}}
                request = common.request(f"{field}.{view}.{order}", SYSTEM, task, 12, [field])
                yield {"field": field, "view": view, "order": order, "required": required,
                       "identifiers": identifiers, "request": request, "original": original}


def grade(case, output):
    words = output["output"].split()
    abstains = output["ended"] and words == ["NONE"]
    chosen = set(words)
    valid = output["ended"] and (abstains or len(words) == len(chosen) == 2 and chosen <= case["identifiers"].keys())
    owner_error = valid and not abstains and any(case["identifiers"][k][0] != case["field"] for k in chosen)
    complete = bool(valid and not abstains and case["required"] and case["required"] == chosen)
    return {
        "reply": output["output"], "expected": sorted(case["required"]), "valid_syntax": bool(valid),
        "scope_violation": bool(owner_error), "full_payload": complete,
        "correct": complete if case["required"] else bool(abstains),
        "exact_source_span": case["original"] if complete else None,
        "insufficient_but_sent": bool(valid and not abstains and not complete),
    }


def locks():
    paths = (Path(__file__), Path(transport.__file__), Path(common.__file__), Path(runner.__file__),
             transport.unifil.TASK, common.TASK, transport.OUT / "transcript.jsonl")
    return {str(p.resolve().relative_to(transport.unifil.ROOT)): runner.digest(p) for p in paths}


def episode(generate):
    outputs = generate([t["request"] for t in tests()])
    return [{"family": NAME, "final": outputs}]


def run(model, directory):
    assert len(list(tests())) == 18
    with patch.multiple(runner, episode=episode, locks=locks):
        runner.run(model, directory)


def assess(directory, exact):
    path = directory / "transcript.jsonl"
    launch = json.loads((directory / "launch.json").read_text())
    complete = json.loads((directory / "complete.json").read_text())
    assert launch["sha256"] == locks() and runner.digest(path) == complete["transcript_sha256"]
    raw = list(map(json.loads, path.read_text().splitlines()))
    decisions, notes = {}, {}
    for case, row in zip(tests(), raw, strict=True):
        assert all(row[k] == v for k, v in case["request"].items())
        ident = row["id"]
        decisions[ident] = grade(case, row)
        if decisions[ident]["full_payload"]:
            notes[case["field"], case["order"]] = case["original"]
    final = directory / "final-records.json"
    assert len(raw) == complete["records"] == 18 and runner.digest(final) == complete["final_records_sha256"]
    assert json.loads(final.read_text()) == {NAME: {r["id"]: r["output"] for r in raw}}

    # The relationship test is reused only when the accepted text is byte-identical.
    _, original, old_notes = transport.replay(transport.OUT)
    actual_notes = dict(notes)
    for key, note in actual_notes.items():
        assert note == old_notes[key]
    comparison = {}
    for tag, prior in original.items():
        _, view, order = tag.split(".")
        received = [k for k in ("brazil", "china") if (k, order) in notes and (view == "intact" or k == "brazil")]
        comparison[tag] = {**prior, "accepted": prior["accepted"] and received == prior["receipt_ids"],
                           "receipt_ids": received, "reused_only_if_identical": received == prior["receipt_ids"]}
    with patch.object(transport, "replay", return_value=(decisions, comparison, notes)):
        replay = review.summarize(directory, exact)
    return {**replay, "scope": "Sentence-ID extraction from authored evidence. Freeze rendering and routing. "
                              "Reuse earlier model comparison only for identical delivered evidence.",
            "comparison_transcript_sha256": runner.digest(transport.OUT / "transcript.jsonl")}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("run", "assess"))
    p.add_argument("--model", type=Path)
    p.add_argument("--directory", type=Path, default=OUT)
    p.add_argument("--exact", action="store_true")
    args = p.parse_args()
    if args.mode == "run":
        run(args.model, args.directory)
    else:
        print(json.dumps(assess(args.directory, args.exact), indent=2, ensure_ascii=False))
