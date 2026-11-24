"""Compare fresh continuations from the same archived Gulf workshop prefix."""

import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research/council_workshop"))

from codex_runner import CodexRunner
from held_suite import metrics
from recording import Recording, decision_request
from replay import replay
from run import EXCLUSION_PRIORITY, pretty, simulate


SOURCE = HERE.parent / "council-workshop-held-pilot-20261123" / "all-sol"
HEADROOM = HERE.parent / "council-workshop-budget-headroom-20261123" / "results.json"
ARMS = ("standard", "priority")


def read(path):
    return json.loads(path.read_text())


def plan():
    archived = replay(SOURCE)
    settings = read(SOURCE / "settings.json")
    row, = [row for row in read(HEADROOM)["meetings"] if row["path"] == SOURCE.relative_to(ROOT).as_posix()]
    cut = row["first_proven_budget_failure"]
    assert (cut["speech"], cut["calls_used"], cut["seat"]) == (6, 15, "NOR")
    assert settings["model"] == "gpt-6.1-sol" and not settings.get("seat_models")
    return {"case_path": SOURCE.relative_to(ROOT).as_posix(), "reused_calls": cut["calls_used"] - 1,
            "target_speech": cut["speech"], "target_seat": cut["seat"], "model": settings["model"],
            "turn_cap": settings["turn_cap"], "call_cap": settings["call_cap"], "priority_suffix": EXCLUSION_PRIORITY,
            "archived_action": archived["history"][cut["speech"] - 1]}


def continue_meeting(arm, design, respond, *, auto_certify=False, source=SOURCE):
    settings = read(source / "settings.json")
    archived = Recording(source)
    reused = 0
    fresh = 0

    def decide(seat, prompt, schema):
        nonlocal reused, fresh
        request = decision_request(settings, seat, prompt, schema)
        if reused < design["reused_calls"]:
            answer = archived.take(request)
            if answer is None:
                raise ValueError("The shared prefix ended early")
            reused += 1
            return answer
        if fresh == 0:
            assert seat == design["target_seat"] and archived.take(request) is not None
            if arm == "priority":
                request["prompt"] += "\n\n" + design["priority_suffix"]
        fresh += 1
        return respond(request)

    result = simulate(settings["case"], settings["countries"], settings["mode"], design["turn_cap"],
                      settings["vote"], decide, call_cap=design["call_cap"], auto_certify_impasse=auto_certify)
    assert reused == design["reused_calls"] and fresh + reused == result["calls"]
    output = {"arm": arm, "reused_calls": reused, "fresh_calls": fresh,
              "fresh_speeches": result["history"][design["target_speech"] - 1:], **metrics(result, settings["case"])}
    if auto_certify:
        output["certificate_source"] = result.get("certificate_source")
    return output


def run(arm, design, *, source=SOURCE, directory=HERE):
    runner = CodexRunner(design["model"], timeout=90)
    with (directory / f"{arm}.jsonl").open("x") as handle:
        def record(request):
            handle.write(json.dumps(request, ensure_ascii=False) + "\n")
            handle.flush()
            try:
                reply = runner(request["prompt"], request["schema"])
            except (OSError, TimeoutError, ValueError, RuntimeError) as error:
                handle.write(json.dumps({"event": "error", "message": str(error)}) + "\n")
                raise
            handle.write(json.dumps({"event": "response", "answer": reply}, ensure_ascii=False) + "\n")
            handle.flush()
            return reply

        result = continue_meeting(arm, design, record, source=source)
    with (directory / f"{arm}-result.json").open("x") as handle:
        handle.write(pretty(result) + "\n")
    return result


def replay_arm(arm, design, *, auto_certify=False, source=SOURCE, directory=HERE):
    events = iter(map(json.loads, (directory / f"{arm}.jsonl").read_text().splitlines()))

    def record(request):
        assert next(events) == request
        reply = next(events)
        assert reply["event"] == "response"
        return reply["answer"]

    result = continue_meeting(arm, design, record, auto_certify=auto_certify, source=source)
    if not auto_certify:
        assert next(events, None) is None and result == read(directory / f"{arm}-result.json")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "run", "replay", "moderator"))
    parser.add_argument("arm", nargs="?", choices=ARMS)
    args = parser.parse_args()
    design = plan()
    if args.command == "plan":
        print(pretty(design))
    else:
        assert design == read(HERE / "plan.json")
        if args.command == "moderator":
            rows = {}
            for arm in ARMS:
                original = replay_arm(arm, design)
                closed = replay_arm(arm, design, auto_certify=True)
                assert closed["fresh_speeches"] == original["fresh_speeches"][:len(closed["fresh_speeches"])]
                assert closed["calls"] <= original["calls"]
                rows[arm] = closed
            print(pretty(rows))
        elif args.arm is None:
            parser.error("Choose one arm")
        else:
            print(pretty(run(args.arm, design) if args.command == "run" else replay_arm(args.arm, design)))
