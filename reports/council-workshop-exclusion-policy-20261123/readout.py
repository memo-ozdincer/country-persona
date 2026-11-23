"""Replay the whole-meeting prompt comparison on the registered Iraq cases."""

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "research/council_workshop"))

from held_suite import exclusion_trace, identify, metrics
from meeting import PACKAGE_SPEECH
from replay import replay
from run import EXCLUSION_PRIORITY, pretty


def load(path, world, priority):
    settings = json.loads((path / "settings.json").read_text())
    assert settings.get("prioritize_exclusions", False) is priority
    assert identify(settings)[:2] == ("iraq", world)
    original_plan = HERE.parent / "council-workshop-exclusion-prompt-20261123" / "plan.json"
    probes = json.loads(original_plan.read_text())
    assert probes["iraq-priority"]["prompt"] == probes["iraq-original"]["prompt"] + "\n\n" + EXCLUSION_PRIORITY
    events = [json.loads(line) for line in (path / "calls.jsonl").read_text().splitlines()]
    assert all(not event["reused"] for event in events if event["event"] == "response")
    for event in events:
        if event["event"] == "request":
            assert event["prompt"].endswith(EXCLUSION_PRIORITY) == (priority and event["schema"] == PACKAGE_SPEECH)
    result = replay(path)
    trace = exclusion_trace(result, settings["case"], settings["countries"])
    return settings, {**metrics(result, settings["case"]), "exclusion_trace": trace}


def compare(world, reference):
    baseline, control = load(reference, world, False)
    treatment, intervention = load(HERE / f"iraq-{world}-priority", world, True)
    remove = {"started", "prioritize_exclusions"}
    assert {k: v for k, v in baseline.items() if k not in remove} == {
        k: v for k, v in treatment.items() if k not in remove
    }
    return {"standard_instruction": control, "exclusions_first": intervention}


if __name__ == "__main__":
    original = HERE.parent / "council-workshop-iraq-pilot-20261123" / "all-sol"
    print(pretty({"impasse": compare("impasse", original),
                  "feasible": compare("feasible", HERE / "iraq-feasible-standard")}))
