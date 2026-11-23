"""Freeze and replay a blinded clause-review comparison and factual control."""

import argparse
from copy import deepcopy
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "research/council_workshop"))

from codex_runner import CodexRunner
from meeting import TEXT, choice, response_schema
from replay import replay
from review import HERE as KIT, digest, packet, read, report
from run import pretty


MODEL = "gpt-6.1-sol"
RECORDS = {"record-01": "sol", "record-02": "astra"}
CONTROL = "guard-control"
FALSE_CLAIM = "The Security Council formally adopted this clause on 10 December 2021 by unanimous vote."


def build():
    trials = {}
    for trial, model in RECORDS.items():
        directory = HERE.parent / "council-workshop-20-20261123" / model
        trials[trial] = packet(read(directory / "settings.json"), replay(directory), read(KIT / "climate-review.json"))
    control = deepcopy(trials["record-01"])
    del control["id"]
    control["answer"] += " " + FALSE_CLAIM
    trials[CONTROL] = {"id": f"clause-{digest(control)[:16]}", **control}
    return {"model": MODEL, "instruction": (KIT / "clause-judge.md").read_text(), "packets": trials}


def schema(packet):
    citation = response_schema(block=choice(*(row["id"] for row in packet["evidence"])), quote=TEXT)
    citations = {"type": "array", "items": citation}
    unit = response_schema(id=choice(*(row["id"] for row in packet["rubric"])),
                           status=choice("met", "unmet", "uncertain"), source=citations, response=TEXT, reason=TEXT)
    guard = response_schema(status=choice("clear", "failed", "uncertain"), source=citations, response=TEXT, reason=TEXT)
    return response_schema(id=choice(packet["id"]), units={"type": "array", "items": unit}, guard=guard)


def score(design):
    rows = {}
    for name, blind_packet in design["packets"].items():
        path = HERE / f"{name}.json"
        if not path.is_file():
            continue
        record = read(path)
        if "call_error" in record:
            rows[name] = record
            continue
        verdict = record["verdict"]
        if name == CONTROL:
            result = {"draft": blind_packet["answer"], "version": None, "status": "authored_control", "ballots": {}}
        else:
            model = RECORDS[name]
            result = replay(HERE.parent / "council-workshop-20-20261123" / model)
        try:
            grade = report(blind_packet, verdict, result)
        except (AttributeError, KeyError, TypeError, ValueError) as error:
            rows[name] = {"invalid_verdict": str(error)}
            continue
        rows[name] = {"model_review": grade}
        if name == CONTROL:
            rows[name]["caught_authored_false_claim"] = grade["guard"] == "failed" and FALSE_CLAIM in verdict["guard"]["response"]
            continue
        archived = HERE.parent / "council-workshop-clause-review-20261123"
        reference = read(archived / f"{model}-verdict.json")
        rows[name]["archived_review"] = report(blind_packet, reference, result)
        prior = {unit["id"]: unit["status"] for unit in reference["units"]}
        rows[name]["criterion_agreement"] = sum(unit["status"] == prior[unit["id"]] for unit in verdict["units"])
        rows[name]["disagreements"] = [
            {"criterion": unit["id"], "archived": prior[unit["id"]], "new": unit["status"]}
            for unit in verdict["units"] if unit["status"] != prior[unit["id"]]
        ]
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("build")
    run = commands.add_parser("run")
    run.add_argument("trial", choices=(*RECORDS, CONTROL))
    commands.add_parser("score")
    args = parser.parse_args()
    design = build()
    if args.command == "build":
        print(pretty(design))
        return
    assert design == read(HERE / "packets.json")
    if args.command == "score":
        print(pretty(score(design)))
        return
    blind_packet = design["packets"][args.trial]
    prompt = design["instruction"] + "\n" + pretty(blind_packet)
    runner = CodexRunner(MODEL, timeout=90)
    with (HERE / f"{args.trial}.json").open("x") as handle:
        try:
            record = {"verdict": runner(prompt, schema(blind_packet))}
        except (OSError, TimeoutError, ValueError, RuntimeError) as error:
            record = {"call_error": str(error)}
        handle.write(pretty(record) + "\n")
    print(pretty(score(design)[args.trial]))


if __name__ == "__main__":
    main()
