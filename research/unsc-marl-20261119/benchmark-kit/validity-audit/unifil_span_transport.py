"""Test exact source selection and protected scope transport with frozen Qwen."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import unifil_final_transfer as unifil

common, runner = unifil.common, unifil.common.runner
NAME = "unifil-span-transport"
OUT = common.OUT / NAME
FIT = common.OUT / "unifil-rubric-fit/fit.json"
ORDERS = {
    "forward": ("full", "partial", "altered", "absent"),
    "reverse": ("absent", "altered", "partial", "full"),
}
FIELDS = {
    "brazil": {
        "question": "Keep Brazil's support for UNIFIL, its view on operating freely, and the precise scope of the Lebanese concerns addressed.",
        "edit": ("some of Lebanon's concerns", "all of Lebanon's concerns"),
    },
    "china": {
        "question": "Keep China's support for UNIFIL, whether the text fully addressed Lebanon's concerns, and China's position on host-State sovereignty or consent.",
        "edit": ("did not fully address", "fully addressed"),
    },
    "russia": {
        "question": "Keep Russia's reason for abstaining, what happened to the prior compromise, and whether it still supported the mission.",
        "edit": ("lost a prior compromise", "preserved a prior compromise"),
    },
    "may": {
        "question": "Keep the date, symbol and standalone stage of the May draft, including vote tally and the reason the draft failed.",
        "edit": ("failed to obtain the required votes", "received the required votes but was vetoed"),
    },
}
SYSTEM = (
    "You are a source holder transmitting one exact passage. Select the option that occurs verbatim in the named "
    "source and includes all the information requested. Ignore other supplied sources. If no option includes every "
    "requested fact verbatim, select the option for insufficient evidence. Output only a single choice letter."
)
RELATIONS = {
    "joint": "Both supported UNIFIL's work. Brazil said the text addressed some Lebanese concerns and China said it did not fully address them.",
    "partial": "Both supported the resolution as adopted.",
    "altered": "Brazil and China disagreed on whether UNIFIL's work should continue.",
    "absent": "Insufficient evidence from the two national source holders.",
}
RELATION_SYSTEM = (
    "You are organizing two source receipts for an official record. Select the complete comparison that is supported "
    "by a receipt from each of Brazil and China. If one receipt is unavailable or none of the comparisons is supported, "
    "select the option for insufficient evidence. Output only a single choice letter."
)


def get_sources():
    return {**{k: unifil.sources()[k] for k in unifil.FIELDS}, "may": common.blocks()["may-final"]}


def source_options(field):
    exact = get_sources()[field]
    short, _ = exact.split(". ", 1)
    old, new = FIELDS[field]["edit"]
    assert exact.count(old) == 1
    return {"full": exact, "partial": short + ".", "altered": exact.replace(old, new),
            "absent": "Insufficient evidence in the named source."}


def make_probes():
    for field, definition in FIELDS.items():
        options = source_options(field)
        views = {"intact": options["full"], "missing": options["partial"]}
        if field == "brazil":
            views["misattributed"] = options["partial"]
        for view, source in views.items():
            for order, kinds in ORDERS.items():
                choices = dict(zip("ABCD", kinds, strict=True))
                payload = {"task": definition["question"], "named_source": {field: source},
                           "options": {letter: options[k] for letter, k in choices.items()}}
                if view == "misattributed":
                    payload["other_source"] = {"unverified attribution": options["full"]}
                yield {"field": field, "view": view, "order": order, "choices": choices, "options": options,
                       "source": source, "expected": "full" if view == "intact" else "absent",
                       "request": common.request(f"{field}.{view}.{order}", SYSTEM, payload, 12, [field])}


def adjudicate(probe, response):
    label = probe["choices"].get(response["output"]) if response["ended"] else None
    option = probe["options"].get(label)
    licensed = label not in (None, "absent") and option in probe["source"]
    accepted = bool(licensed and label == "full")
    return {"choice": label, "expected": probe["expected"], "correct": label == probe["expected"],
            "exact_source_span": option if licensed else None, "full_payload": accepted,
            "unsupported_attempt": label not in (None, "absent") and not licensed,
            "incomplete_attempt": bool(licensed and label == "partial")}


def relation_probes(notes):
    for order in ORDERS:
        for view in ("intact", "missing"):
            received = {k: notes[(k, order)] for k in ("brazil", "china")
                        if notes.get((k, order)) and (view == "intact" or k != "china")}
            choices = dict(zip("ABCD", ("joint", "partial", "altered", "absent") if order == "forward"
                               else ("absent", "altered", "partial", "joint"), strict=True))
            payload = {"receipts": received, "options": {letter: RELATIONS[k] for letter, k in choices.items()}}
            yield {"view": view, "order": order, "choices": choices, "receipts": received,
                   "expected": "joint" if len(received) == 2 else "absent",
                   "request": common.request(f"comparison.{view}.{order}", RELATION_SYSTEM,
                                             payload, 12, list(received))}


def interpret_sources(probes, rows):
    decisions, notes = {}, {}
    for probe in probes:
        ident = probe["request"]["id"]
        result = adjudicate(probe, rows[ident])
        decisions[ident] = result
        if probe["view"] == "intact" and result["full_payload"]:
            notes[probe["field"], probe["order"]] = result["exact_source_span"]
    return decisions, notes


def locks():
    paths = (Path(__file__), Path(unifil.__file__), Path(common.__file__), Path(runner.__file__),
             unifil.TASK, common.TASK, FIT)
    return {str(p.resolve().relative_to(unifil.ROOT)): runner.digest(p) for p in paths}


def check():
    probes = list(make_probes())
    assert len(probes) == 18 and len({p["request"]["id"] for p in probes}) == 18
    for test in probes:
        options = test["options"]
        assert options["altered"] not in test["source"] and options["partial"] in test["source"]
        assert (options["full"] in test["source"]) == (test["expected"] == "full")
    return {"source_probes": len(probes), "comparison_probes": 4, "fields": list(FIELDS)}


def episode(generate):
    probes = list(make_probes())
    source = generate([p["request"] for p in probes])
    _, notes = interpret_sources(probes, source)
    comparison = generate([p["request"] for p in relation_probes(notes)])
    return [{"family": NAME, "final": {**source, **comparison}}]


def run(model, directory):
    check()
    with patch.multiple(runner, episode=episode, locks=locks):
        runner.run(model, directory)


def replay(directory):
    launch = json.loads((directory / "launch.json").read_text())
    end = json.loads((directory / "complete.json").read_text())
    path = directory / "transcript.jsonl"
    rows = list(map(json.loads, path.read_text().splitlines()))
    recorded = {r["id"]: r for r in rows}
    assert len(rows) == len(recorded) == end["records"] == 22
    assert launch["sha256"] == locks() and end["transcript_sha256"] == runner.digest(path)
    probes = list(make_probes())
    decisions, notes = interpret_sources(probes, recorded)
    comparisons = {}
    relation = list(relation_probes(notes))
    for p in relation:
        response = recorded[p["request"]["id"]]
        chose = p["choices"].get(response["output"]) if response["ended"] else None
        comparisons[p["request"]["id"]] = {"choice": chose, "expected": p["expected"], "correct": chose == p["expected"],
                                           "receipt_ids": list(p["receipts"]),
                                           "accepted": chose == p["expected"] == "joint"}
    for actual, expected in zip(rows, [p["request"] for p in [*probes, *relation]], strict=True):
        assert all(actual[k] == v for k, v in expected.items())
    final = directory / "final-records.json"
    assert end["final_records_sha256"] == runner.digest(final)
    assert json.loads(final.read_text()) == {NAME: {r["id"]: r["output"] for r in rows}}
    return decisions, comparisons, notes


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "replay"))
    cli.add_argument("--directory", type=Path, default=OUT)
    cli.add_argument("--model", type=Path)
    opt = cli.parse_args()
    if opt.mode == "check":
        print(json.dumps(check(), indent=2))
    elif opt.mode == "run":
        if opt.model is None:
            cli.error("run needs --model")
        run(opt.model, opt.directory)
    else:
        decisions, comparisons, _ = replay(opt.directory)
        assert unifil.replay_util.replay_tokens(opt.directory) == len(decisions) + len(comparisons)
        print(json.dumps({"sources": decisions, "comparisons": comparisons}, indent=2, ensure_ascii=False))
