"""Measure necessary completion budgets along the registered all-Sol traces."""

from collections import Counter
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research/council_workshop"))

from held_suite import SOL, checked_exchange, identify, metrics
from mandates import Mandates
from meeting import PACKAGE_SPEECH, Meeting
from recording import Recording, decision_request
from replay import replay
from run import pretty, simulate
from scorecard import registered_paths


def minimum_speeches(state, feasible):
    if state.status != "open":
        return 0
    if feasible:
        if state.draft in feasible:
            return len(state.countries) - len(state.accepted)
        return 1 + len(state.countries)
    return len(state.mandates.options) - len(state.exclusions) + 1


def holder_deadlines(state, feasible):
    if feasible or state.status != "open":
        return {}
    sole_holders = Counter()
    for label in state.mandates.options.keys() - state.exclusions.keys():
        holders = [seat for seat in state.countries if label not in state.mandates.allowed[seat]]
        if len(holders) == 1:
            sole_holders[holders[0]] += 1
    deadlines = {}
    for seat in state.countries:
        if seat not in sole_holders:
            continue
        first_turn = state.queue.index(seat) + 1 if seat in state.queue else len(state.queue) + 1
        deadlines[seat] = {"first_possible_speech_offset": first_turn, "required_exclusions": sole_holders[seat],
                           "minimum_offset_for_declaration": first_turn + sole_holders[seat]}
    return deadlines


def audit_trace(path, settings):
    result = replay(path)
    family, world, _, order = identify(settings)
    assert settings["mode"] == "meeting" and not settings["vote"] and not settings.get("auto_certify_impasse")
    mandates = Mandates.from_case(settings["case"], order)
    feasible = {mandates.options[label] for label in result["mandate_score"]["feasible_packages"]}
    events = [json.loads(line) for line in (path / "calls.jsonl").read_text().splitlines()]
    cuts = []
    for call_number, (request, response) in enumerate(zip(events[::2], events[1::2], strict=True), 1):
        if request["schema"] != PACKAGE_SPEECH:
            continue
        packet, _ = json.JSONDecoder().raw_decode(request["prompt"][request["prompt"].index("{"):])
        public = packet["public"]
        state = Meeting(order, mandates=mandates, **{key: val for key, val in public.items() if key != "options"})
        state.apply(request["country"], response["answer"])
        turn = len(state.history)
        speeches_needed = minimum_speeches(state, feasible)
        # The engine polls every seat outside the queue again before the next speech.
        # After any subsequent speech its speaker is outside the queue, so at least one poll is needed.
        first_poll = len(order) - len(state.queue) if speeches_needed else 0
        calls_needed = first_poll + speeches_needed + max(0, speeches_needed - 1)
        remaining_speeches = settings["turn_cap"] - turn
        remaining_calls = settings["call_cap"] - call_number
        holders = holder_deadlines(state, feasible)
        blockers = []
        if speeches_needed > remaining_speeches:
            blockers.append("speech_budget")
        if calls_needed > remaining_calls:
            blockers.append("call_budget")
        if any(holder["minimum_offset_for_declaration"] > remaining_speeches for holder in holders.values()):
            blockers.append("sole_holder_cannot_finish_before_cap")
        if state.status != "open" and not mandates.score(state.status, state.draft)["reward"]:
            blockers.append("failed_terminal_outcome")
        cuts.append({"speech": turn, "calls_used": call_number, "seat": request["country"],
                     "action": response["answer"]["action"], "exclusions": state.exclusions, "queue": state.queue,
                     "remaining_speeches": remaining_speeches, "remaining_calls": remaining_calls,
                     "minimum_further_speeches": speeches_needed, "mandatory_next_floor_polls": first_poll,
                     "minimum_further_calls": calls_needed, "sole_holder_deadlines": holders, "blockers": blockers})

    assert len(cuts) == len(result["history"])
    first = next((row for row in cuts if row["blockers"]), None)
    assert not result["mandate_score"]["reward"] or first is None
    return {"family": family, "world": world, "order": order, "outcome": result["mandate_score"]["outcome"],
            "path": path.relative_to(ROOT).as_posix(), "first_proven_budget_failure": first, "after_speeches": cuts}


def gulf_suffix(row):
    path = ROOT / row["path"]
    settings = json.loads((path / "settings.json").read_text())
    archive = Recording(path)
    cut = row["first_proven_budget_failure"]
    reuse_limit = cut["calls_used"] - 1
    reused = 0

    def decide(seat, prompt, schema):
        nonlocal reused
        if reused == reuse_limit:
            return checked_exchange(seat, prompt, schema)
        answer = archive.take(decision_request(settings, seat, prompt, schema))
        if answer is None:
            raise ValueError("Missing a recorded decision before the scripted suffix")
        reused += 1
        return answer

    case = settings["case"]
    result = simulate(case, row["order"], "meeting", settings["turn_cap"], False, decide, call_cap=settings["call_cap"])
    assert reused == reuse_limit and result["mandate_score"]["reward"] == 1
    return {**metrics(result, case), "reused_calls": reused, "scripted_speeches": result["history"][cut["speech"] - 1:]}


if __name__ == "__main__":
    rows = []
    for path in registered_paths():
        settings = json.loads((path / "settings.json").read_text())
        if settings["model"] == SOL and not settings.get("seat_models"):
            rows.append(audit_trace(path, settings))
    assert len(rows) == 8 and len({(r["family"], r["world"], r["order"][0]) for r in rows}) == 8
    gulf, = [r for r in rows if (r["family"], r["world"], r["order"][0]) == ("guinea", "impasse", "GHA")]
    print(pretty({"meetings": rows, "gulf_scripted_suffix": gulf_suffix(gulf)}))
