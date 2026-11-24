"""Replay registered meetings under direct floor handoff using exact request matches."""

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research/council_workshop"))

from held_suite import identify, metrics
from meeting import FLOOR, PACKAGE_SPEECH
from recording import decision_request
from replay import replay
from run import pretty, simulate
from scorecard import endpoint, registered_paths


class UnrecordedDecision(Exception):
    pass


def compare(directory, settings, respond=None):
    family, world, _, order = identify(settings)
    original = replay(directory)
    archive = list(map(json.loads, (directory / "calls.jsonl").read_text().splitlines()))
    decisions = list(zip(archive[::2], archive[1::2], strict=True))
    index = 0
    reused = 0
    bypassed = []
    missing = None
    fresh = []

    def recorded(seat, prompt, schema):
        nonlocal index, reused, missing
        request = decision_request(settings, seat, prompt, schema)
        start = index
        if index < len(decisions) and decisions[index][0] != request and schema == PACKAGE_SPEECH:
            packet, _ = json.JSONDecoder().raw_decode(prompt[prompt.index("{"):])
            public = packet["public"]
            if public["exclusions"].keys() == public["options"].keys():
                while index < len(decisions) and decisions[index][0]["schema"] == FLOOR:
                    poll, reply = decisions[index]
                    bypassed.append({"original_call": index + 1, "seat": poll["country"],
                                     "action": reply["answer"]["action"]})
                    index += 1
        if index == len(decisions) or decisions[index][0] != request:
            missing = {"variant_call": reused + 1, "seat": seat, "next_original_call": index + 1
                       if index < len(decisions) else None}
            if index == start:
                raise ValueError(f"Unexpected divergence before bypassing a poll in {directory}")
            if respond is None:
                raise UnrecordedDecision
            if index != len(decisions) - 1:
                raise ValueError("The live comparison requires a recorded final decision")
            answer = respond(request, decisions[index])
            fresh.append({"seat": seat, "answer": answer})
            index += 1
            return answer
        reply = decisions[index][1]["answer"]
        index += 1
        reused += 1
        return reply

    try:
        routed = simulate(settings["case"], order, settings["mode"], settings["turn_cap"], settings["vote"],
                          recorded, call_cap=settings["call_cap"], skip_poll_after_certificate=True)
    except UnrecordedDecision:
        routed = None
    if routed is not None:
        assert index == len(decisions) and routed["calls"] == reused + len(fresh)
        shared_speeches = len(routed["history"]) - len(fresh)
        assert routed["history"][:shared_speeches] == original["history"][:shared_speeches]
        if not fresh:
            assert routed["history"] == original["history"]
            assert original["calls"] == reused + len(bypassed)
            assert routed["mandate_score"] == original["mandate_score"]
    return {"family": family, "world": world, "order": order, "seat_models": settings.get("seat_models", {}),
            "path": directory.relative_to(ROOT).as_posix(),
            "original": endpoint(metrics(original, settings["case"])),
            "variant": (endpoint(metrics(routed, settings["case"]))
                        if routed is not None else None),
            "reused_calls": reused, "bypassed_polls": bypassed, "first_unrecorded_decision": missing,
            **({"fresh_decisions": fresh} if fresh else {})}


def audit():
    completed = []
    interrupted = []
    for path in registered_paths():
        settings = json.loads((path / "settings.json").read_text())
        if (path / "result.json").is_file():
            completed.append(compare(path, settings))
        else:
            interrupted.append(path.relative_to(ROOT).as_posix())
    return {"meetings": completed, "interrupted_paths": interrupted,
            "complete_variant_replays": sum(row["variant"] is not None for row in completed),
            "total_polls_bypassed": sum(len(row["bypassed_polls"]) for row in completed)}


if __name__ == "__main__":
    print(pretty(audit()))
