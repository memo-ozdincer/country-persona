"""Retrieve each required proof sentence independently, then check the bundle."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import unifil_sentence_extraction as previous
import unifil_span_transport as transport

common, runner = transport.common, transport.runner
NAME = "unifil-slot-extraction"
OUT = common.OUT / NAME
SYSTEM = (
    "Find one sentence that explicitly answers the question and is attributed to the named owner. "
    "A vote alone does not explain a view or give its rationale. Do not infer missing evidence from votes, "
    "other owners or background knowledge. Reply with exactly the matching sentence ID, or NONE if absent."
)
QUESTIONS = {
    "brazil": {"first": "Which sentence states Brazil's support for UNIFIL's continuing work?",
               "second": "Which sentence gives Brazil's view on UNIFIL's freedom to operate and the degree to which the text addressed Lebanese concerns?"},
    "china": {"first": "Which sentence states China's support for the mission and its assessment of the text's treatment of Lebanon's concerns?",
              "second": "Which sentence gives China's principle about sovereignty or consent in peacekeeping?"},
    "russia": {"first": "Which sentence gives Russia's reason for abstaining and what happened to the earlier compromise?",
               "second": "Which sentence states Russia's continuing support for the mission and call for coordination?"},
    "may": {"first": "Which sentence identifies the date and instrument of the separate May vote?",
            "second": "Which sentence gives the tally of the May vote and why the draft failed?"},
}


def views():
    yield from previous.tests()
    for case in previous.tests():
        if case["view"] != "intact":
            continue
        remain = {k: v for k, v in case["identifiers"].items() if v[2] != "first"}
        yield {**case, "view": "missing-first", "identifiers": remain}


def tests():
    for view in views():
        field = view["field"]
        for slot, question in QUESTIONS[field].items():
            options = {k: {"owner": value[0], "text": value[1]} for k, value in view["identifiers"].items()}
            gold = [k for k, row in view["identifiers"].items() if row[0] == field and row[2] == slot]
            assert len(gold) <= 1
            tag = ".".join((field, view["view"], view["order"], slot))
            payload = {"owner": field, "question": question, "sentences": options}
            request = common.request(tag, SYSTEM, payload, 8, [field])
            yield {"view": view, "slot": slot, "gold": (gold or ["NONE"])[0], "request": request}


def locks():
    files = (Path(__file__), Path(previous.__file__), Path(transport.__file__), Path(runner.__file__),
             Path(common.__file__), transport.unifil.TASK, common.TASK)
    return {str(p.resolve().relative_to(transport.unifil.ROOT)): runner.digest(p) for p in files}


def episode(generate):
    calls = [t["request"] for t in tests()]
    assert len(calls) == 52 and len({r["id"] for r in calls}) == 52
    replies = {}
    for start in range(0, len(calls), 13):
        replies.update(generate(calls[start:start+13]))
    return [{"family": NAME, "final": replies}]


def run(model, directory):
    with patch.multiple(runner, episode=episode, locks=locks):
        runner.run(model, directory)


def replay(directory):
    path = directory / "transcript.jsonl"
    launch = json.loads((directory / "launch.json").read_text())
    complete = json.loads((directory / "complete.json").read_text())
    assert launch["sha256"] == locks() and runner.digest(path) == complete["transcript_sha256"]
    raw = list(map(json.loads, path.read_text().splitlines()))
    slots, bundles = {}, {}
    for test, row in zip(tests(), raw, strict=True):
        assert all(row[k] == v for k, v in test["request"].items())
        ident, expected, v = row["id"], test["gold"], test["view"]
        actual = row["output"] if row["ended"] else None
        chosen = v["identifiers"].get(actual)
        mark = {
            "slot": test["slot"], "actual": actual, "expected": expected, "correct": actual == expected,
            "valid_syntax": actual == "NONE" or actual in v["identifiers"],
            "wrong_owner": bool(chosen and chosen[0] != v["field"]),
            "supported_slot": expected != "NONE" and actual == expected,
        }
        slots[ident] = mark
        key = ident.rsplit(".", 1)[0]
        bundles.setdefault(key, {})[test["slot"]] = mark
    for key, parts in bundles.items():
        assert tuple(parts) == ("first", "second"), key
    bundle_result = {key: {"released": all(r["supported_slot"] for r in parts.values()),
                           "correct": all(r["correct"] for r in parts.values()),
                           "unsafe_if_ungated": any(r["wrong_owner"] or
                                (r["expected"] == "NONE" and r["actual"] not in (None, "NONE")) for r in parts.values())}
                     for key, parts in bundles.items()}
    final = directory / "final-records.json"
    assert len(raw) == complete["records"] == 52 and runner.digest(final) == complete["final_records_sha256"]
    assert json.loads(final.read_text()) == {NAME: {r["id"]: r["output"] for r in raw}}
    return slots, bundle_result


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "replay"))
    cli.add_argument("--model", type=Path)
    cli.add_argument("--directory", type=Path, default=OUT)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.model, args.directory)
    else:
        slots, bundles = replay(args.directory)
        assert transport.unifil.replay_util.replay_tokens(args.directory) == len(slots)
        print(json.dumps({"slots": slots, "bundles": bundles}, indent=2))
