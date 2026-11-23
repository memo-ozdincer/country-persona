"""Search all legal completions of the archived impasse prefixes under both caps."""

import json
from functools import lru_cache
from itertools import combinations
from pathlib import Path
from runpy import run_path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research/council_workshop"))

from held_suite import metrics
from mandates import Mandates
from meeting import FLOOR
from recording import Recording, decision_request
from replay import replay
from run import pretty, simulate


def read(path):
    return json.loads(path.read_text())


def completion_search(order, mandates):
    @lru_cache(maxsize=None)
    def search(last, queue, missing, speeches_left, calls_left):
        # Each missing exclusion and the declaration uses one speech.
        required = len(missing) + 1
        if required > speeches_left:
            return None
        start = order.index(last) + 1
        polled = tuple(seat for seat in order[start:] + order[:start] if seat not in queue)
        if len(polled) + 2 * required - 1 > calls_left:
            return None
        remaining_calls = calls_left - len(polled) - 1
        if not missing and queue:
            return (((), queue[0], "declare_impasse", ""),)

        # Poll order is fixed. Only the subset of requests can vary. Longer queues
        # come first to find low-poll witnesses early, without claiming optimality.
        for size in range(len(polled), -1, -1):
            for requested in combinations(polled, size):
                next_queue = queue + requested
                if not next_queue:
                    continue
                speaker, *waiting = next_queue
                if not missing:
                    return ((requested, speaker, "declare_impasse", ""),)
                exclusions = tuple(label for label in missing if label not in mandates.allowed[speaker])
                actions = [("rule_out", label) for label in exclusions] + [("yield_floor", "")]
                for action, label in actions:
                    suffix = search(speaker, tuple(waiting), tuple(key for key in missing if key != label),
                                    speeches_left - 1, remaining_calls)
                    if suffix is not None:
                        return ((requested, speaker, action, label), *suffix)
        return None

    return search


def replay_witness(path, settings, cut, witness):
    archive = Recording(path)
    reused = 0
    new_decisions = []

    def decide(seat, prompt, schema):
        nonlocal reused
        if reused < cut["calls_used"]:
            answer = archive.take(decision_request(settings, seat, prompt, schema))
            if answer is None:
                raise ValueError("Archived witness prefix ended early")
            reused += 1
            return answer
        packet, _ = json.JSONDecoder().raw_decode(prompt[prompt.index("{"):])
        public = packet["public"]
        requests, speaker, action, label = witness[len(public["history"]) - cut["speech"]]
        if schema is FLOOR:
            answer = {"action": "request_floor" if seat in requests else "pass"}
        else:
            assert seat == speaker
            answer = {"action": action, "version": public["version"], "text": label or "Record the scripted decision."}
        new_decisions.append({"call": reused + len(new_decisions) + 1, "seat": seat, "answer": answer})
        return answer

    case = settings["case"]
    result = simulate(case, settings["countries"], "meeting", settings["turn_cap"], False, decide,
                      call_cap=settings["call_cap"])
    assert result["status"] == "certified_impasse" and reused == cut["calls_used"]
    assert len(result["history"]) == cut["speech"] + len(witness)
    return {**metrics(result, case), "reused_calls": reused, "floor_and_speech_plan": witness,
            "new_speeches": result["history"][cut["speech"]:], "new_decisions": new_decisions}


def examine(row, audit_trace):
    path = ROOT / row["path"]
    settings = read(path / "settings.json")
    assert audit_trace(path, settings) == row
    original = replay(path)
    order = settings["countries"]
    assert not original["mandate_score"]["feasible_packages"] and not settings["vote"]
    assert not settings.get("auto_certify_impasse")
    mandates = Mandates.from_case(settings["case"], order)
    search = completion_search(order, mandates)
    reachability = []
    last_witness = None
    for cut in row["after_speeches"]:
        if cut["action"] == "declare_impasse":
            assert original["status"] == "certified_impasse"
            reachability.append({"speech": cut["speech"], "reachable": True})
            continue
        missing = tuple(sorted(mandates.options.keys() - cut["exclusions"].keys()))
        found = search(cut["seat"], tuple(cut["queue"]), missing, cut["remaining_speeches"], cut["remaining_calls"])
        assert not (found and cut["blockers"])
        reachability.append({"speech": cut["speech"], "reachable": found is not None})
        if found:
            last_witness = (cut, found)
    statuses = [row["reachable"] for row in reachability]
    assert statuses == sorted(statuses, reverse=True)
    first = next((row["speech"] for row in reachability if not row["reachable"]), None)
    return {"family": row["family"], "order": order, "outcome": row["outcome"], "path": row["path"],
            "first_unreachable_speech": first, "reachability": reachability,
            "last_open_witness": replay_witness(path, settings, *last_witness) if last_witness else None}


if __name__ == "__main__":
    baseline = HERE.parent / "council-workshop-budget-headroom-20261123" / "results.json"
    rebuild = run_path(str(baseline.with_name("audit.py")))["audit_trace"]
    rows = [examine(row, rebuild) for row in read(baseline)["meetings"] if row["world"] == "impasse"]
    assert len(rows) == 4 and len({(row["family"], row["order"][0]) for row in rows}) == 4
    print(pretty({"meetings": rows}))
