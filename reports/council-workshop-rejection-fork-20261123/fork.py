"""Build a matched feasibility fork and probe its shared second speech."""

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "research/council_workshop"))

from codex_runner import CodexRunner
from held_suite import metrics
from mandates import Mandates
from meeting import FLOOR, PACKAGE_SPEECH, Meeting
from run import pretty, simulate

ORDER = ["GHA", "CHN", "NOR"]
TURN_CAP, CALL_CAP = 5, 24
MODEL = "gpt-6.1-sol"
MODES = ("standard", "after-rejection")
WITNESSES = {
    "feasible": [("GHA", "rule_out", "review"), ("CHN", "propose", "briefing"),
                 ("NOR", "accept", "Accept briefing."), ("GHA", "accept", "Accept briefing."),
                 ("CHN", "accept", "Accept briefing.")],
    "impasse": [("GHA", "rule_out", "review"), ("CHN", "rule_out", "coastal"),
                ("NOR", "rule_out", "regional"), ("NOR", "rule_out", "briefing"),
                ("GHA", "declare_impasse", "All packages have checked exclusions.")],
}


def read(path):
    return json.loads(path.read_text())


def packet(prompt):
    return json.JSONDecoder().raw_decode(prompt[prompt.index("{"):])[0]


def build():
    feasible = read(HERE.parent / "council-workshop-rejected-opening-20261123" / "case.json")
    impasse = deepcopy(feasible)
    impasse["mandate_game"]["allowed"]["NOR"].remove("briefing")
    cases = {"feasible": feasible, "impasse": impasse}
    prompts = {}
    runs = {}
    for mode in MODES:
        for name, case in cases.items():
            schedule = WITNESSES[name]
            observed = []

            def decide(country, prompt, schema):
                public = packet(prompt)["public"]
                seat, action, text = schedule[len(public["history"])]
                if schema is FLOOR:
                    return {"action": "request_floor" if country == seat else "pass"}
                assert schema is PACKAGE_SPEECH and country == seat
                if len(public["history"]) == 1:
                    observed.append(prompt)
                return {"action": action, "version": public["version"], "text": text}

            result = simulate(case, ORDER, "meeting", TURN_CAP, False, decide, call_cap=CALL_CAP,
                              prioritize_exclusions_after_rejection=mode == "after-rejection")
            assert result["mandate_score"]["reward"] == 1 and len(observed) == 1
            if mode in prompts:
                assert prompts[mode] == observed[0]
            else:
                prompts[mode] = observed[0]
            if mode == "standard":
                runs[name] = {**metrics(result, case), "history": result["history"]}

    required = {"feasible": {"action": "propose", "package": "briefing"},
                "impasse": {"action": "rule_out", "package": "coastal"}}
    assert {name: run["feasible_packages"] for name, run in runs.items()} == {"feasible": ["briefing"], "impasse": []}
    return {"cases": cases, "turn_cap": TURN_CAP, "call_cap": CALL_CAP, "model": MODEL,
            "seat": "CHN", "speech": 2, "prompts": prompts, "schema": PACKAGE_SPEECH,
            "necessary_next_actions": required, "uniform_world_success_ceiling": 0.5, "scripted_witnesses": runs}


def score(design):
    rows = {}
    for mode in MODES:
        response_path = HERE / f"{mode}.json"
        if not response_path.is_file():
            continue
        response = read(response_path)
        if "call_error" in response:
            rows[mode] = response
            continue
        answer = response["answer"]
        compatible = []
        public = packet(design["prompts"][mode])["public"]
        for name, case in design["cases"].items():
            meeting = Meeting(ORDER, mandates=Mandates.from_case(case, ORDER),
                              **{key: deepcopy(value) for key, value in public.items() if key != "options"})
            try:
                meeting.apply(design["seat"], answer)
            except (AttributeError, KeyError, TypeError, ValueError):
                continue
            if {"action": answer["action"], "package": answer["text"].strip()} == design["necessary_next_actions"][name]:
                compatible.append(name)
        rows[mode] = {"answer": answer, "worlds_still_reachable": compatible,
                      "uniform_world_ceiling_after_choice": len(compatible) / len(design["cases"])}
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("build")
    run = commands.add_parser("run")
    run.add_argument("mode", choices=MODES)
    commands.add_parser("score")
    args = parser.parse_args()
    design = build()
    if args.command == "build":
        print(pretty(design))
        return
    assert design == read(HERE / "fork.json")
    if args.command == "score":
        print(pretty(score(design)))
        return
    runner = CodexRunner(MODEL, timeout=90)
    with (HERE / f"{args.mode}.json").open("x") as handle:
        try:
            response = {"answer": runner(design["prompts"][args.mode], design["schema"])}
        except (OSError, TimeoutError, ValueError, RuntimeError) as error:
            response = {"call_error": str(error)}
        handle.write(pretty(response) + "\n")
    print(pretty(response))


if __name__ == "__main__":
    main()
