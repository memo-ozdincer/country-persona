"""Freeze archived speaking inputs, run one prompt variant, or replay its grade."""

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "research/council_workshop"))

from codex_runner import CodexRunner
from mandates import Mandates
from meeting import Meeting, PACKAGE_SPEECH
from replay import replay
from run import pretty

MODEL = "gpt-6.1-sol"
BASELINES = {
    "iraq": ("council-workshop-iraq-pilot-20261123/all-sol", 13, "FRA"),
    "guinea": ("council-workshop-held-pilot-20261123/feasible-all-sol", 3, "NOR"),
}
PERMISSION = ("You can rule out any still-unexcluded package outside your own mandate, "
              "even while a different package is the current draft.")
PRIORITY = (" If you have such an exclusion to record, use this speech to record one "
            "before proposing or signing a package.")
DESIGN = {
    "iraq-original": ("iraq", "", "rule_out", "closed"),
    "iraq-permission": ("iraq", PERMISSION, "rule_out", "closed"),
    "iraq-priority": ("iraq", PERMISSION + PRIORITY, "rule_out", "closed"),
    "guinea-priority": ("guinea", PERMISSION + PRIORITY, "accept", "briefing"),
}


def read(path):
    return json.loads(path.read_text())


def packet(prompt):
    return json.JSONDecoder().raw_decode(prompt[prompt.index("{"):])[0]


def source_inputs():
    inputs = {}
    for name, (relative, speech, seat) in BASELINES.items():
        directory = HERE.parent / relative
        replay(directory)
        settings = read(directory / "settings.json")
        events = [json.loads(line) for line in (directory / "calls.jsonl").read_text().splitlines()]
        speeches = [(request, response) for request, response in zip(events[::2], events[1::2], strict=True)
                    if request["schema"] == PACKAGE_SPEECH]
        request, response = speeches[speech - 1]
        assert request["country"] == seat and settings["model"] == MODEL and not settings.get("seat_models")
        inputs[name] = (settings, request, response["answer"])
    return inputs


def plan(inputs):
    trials = {}
    for key, (source, reminder, action, package) in DESIGN.items():
        _, request, archived_answer = inputs[source]
        prompt = request["prompt"] + ("\n\n" + reminder if reminder else "")
        trials[key] = {"source": source, "speech": BASELINES[source][1], "seat": request["country"],
                       "model": MODEL, "schema": request["schema"], "prompt": prompt,
                       "reference_answer": archived_answer, "target": {"action": action, "package": package}}
    return trials


def grade(trial, answer, settings):
    public = packet(trial["prompt"])["public"]
    mandates = Mandates.from_case(settings["case"], settings["countries"])
    current = next(label for label, text in mandates.options.items() if text == public["draft"])
    seat = trial["seat"]
    available = sorted(mandates.options.keys() - mandates.allowed[seat] - public["exclusions"].keys())
    meeting = Meeting(settings["countries"], mandates=mandates,
                      **{key: value for key, value in public.items() if key != "options"})
    try:
        meeting.apply(seat, answer)
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        return {"legal": False, "target_met": False, "error": str(error)}
    action = answer["action"]
    chosen = answer["text"].strip() if action in ("rule_out", "propose") else current
    target_met = {"action": action, "package": chosen} == trial["target"]
    return {"legal": True, "target_met": target_met, "current_package": current,
            "available_exclusions": available, "action": action, "package": chosen,
            "locally_compatible_signature": current in mandates.allowed[seat] if action == "accept" else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "run", "score"))
    parser.add_argument("trial", nargs="?", choices=DESIGN)
    args = parser.parse_args()
    inputs = source_inputs()
    expected = plan(inputs)
    if args.command == "plan":
        print(pretty(expected))
        return
    trials = read(HERE / "plan.json")
    if trials != expected:
        raise ValueError("Frozen plan no longer reconstructs from the original transcripts")
    if args.command == "run":
        if args.trial is None:
            parser.error("Select a single trial")
        trial = trials[args.trial]
        runner = CodexRunner(trial["model"], timeout=90)
        with (HERE / f"{args.trial}.json").open("x") as handle:
            try:
                response = {"answer": runner(trial["prompt"], trial["schema"])}
            except (OSError, TimeoutError, ValueError, RuntimeError) as error:
                response = {"call_error": str(error)}
            handle.write(pretty(response) + "\n")
        print(pretty(response))
        return
    scored = {}
    for name, trial in trials.items():
        result_path = HERE / f"{name}.json"
        if not result_path.is_file():
            continue
        result = read(result_path)
        scored[name] = grade(trial, result["answer"], inputs[trial["source"]][0]) if "answer" in result else result
    print(pretty(scored))


if __name__ == "__main__":
    main()
