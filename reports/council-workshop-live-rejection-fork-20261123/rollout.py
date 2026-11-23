"""Replay the six-speech fork with scripted routing and live speech decisions."""

import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
FORK = HERE.parent / "council-workshop-rejection-fork-20261123"
sys.path.insert(0, str(FORK))

from fork import CALL_CAP, FLOOR, MODEL, ORDER, CodexRunner, metrics, packet, pretty, read, simulate

INTERVENTION = "impasse-checked-rejection"

def entries(world):
    return [json.loads(line) for line in (HERE / f"{world}.jsonl").read_text().splitlines()]


def rollout(world, decision):
    intervened = world == INTERVENTION
    case = deepcopy(read(FORK / "fork.json")["cases"]["impasse" if intervened else world])
    case["brief"] = case["brief"].replace("five speaking turns", "six speaking turns")
    assert "six speaking turns" in case["brief"]
    shared = None
    if world != "feasible":
        shared, = [row for row in entries("feasible") if row["source"] == "model" and row["speech"] == 2]
    counts = {"fixed": 0, "model": 0, "reused": 0}
    if intervened:
        counts["substitution"] = 0

    def call(seat, prompt, schema):
        public = packet(prompt)["public"]
        history = public["history"]
        index = len(history)
        # Route from public replies only. Allow one last turn if agreement is late.
        if index < 3:
            speaker = ORDER[index]
        elif history[2]["action"] == "accept":
            speaker = ["GHA", "CHN", "NOR"][index - 3]
        else:
            speaker = ["CHN", "NOR", "GHA"][index - 3]
        request = {"seat": seat, "speech": index + 1, "prompt": prompt, "schema": schema}
        reply = None
        if schema is FLOOR:
            source = "fixed"
            reply = {"action": "request_floor" if seat == speaker else "pass"}
        else:
            assert seat == speaker
            if index == 0:
                source, reply = "fixed", {"action": "rule_out", "version": 1, "text": "review"}
            elif index == 1 and shared is not None:
                assert all(shared[key] == value for key, value in request.items())
                source, reply = "reused", shared["answer"]
            elif index == 2 and intervened:
                original, = [row for row in entries("impasse") if row["source"] == "model" and row["speech"] == 3]
                assert all(original[key] == value for key, value in request.items())
                source, reply = "substitution", {"action": "rule_out", "version": public["version"], "text": "briefing"}
            else:
                source = "model"
        counts[source] += 1
        return decision(request | {"source": source}, reply)

    result = simulate(case, ORDER, "meeting", 6, False, call, call_cap=CALL_CAP)
    assert result["calls"] == sum(counts.values())
    return {**metrics(result, case), "decision_counts": counts, "history": result["history"]}


def run(world):
    model = CodexRunner(MODEL, timeout=90)
    with (HERE / f"{world}.jsonl").open("x") as handle:
        def record(request, reply):
            try:
                answer = model(request["prompt"], request["schema"]) if reply is None else reply
            except (OSError, TimeoutError, ValueError, RuntimeError) as error:
                handle.write(json.dumps(request | {"call_error": str(error)}, ensure_ascii=False) + "\n")
                raise
            handle.write(json.dumps(request | {"answer": answer}, ensure_ascii=False) + "\n")
            handle.flush()
            return answer

        result = rollout(world, record)
    with (HERE / f"{world}-result.json").open("x") as handle:
        handle.write(pretty(result) + "\n")
    return result


def replay(world):
    events = iter(entries(world))

    def recorded(request, reply):
        row = next(events)
        answer = row.pop("answer")
        assert row == request
        assert reply is None or reply == answer
        return answer

    result = rollout(world, recorded)
    assert next(events, None) is None
    assert result == read(HERE / f"{world}-result.json")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "replay"))
    parser.add_argument("world", choices=("feasible", "impasse", INTERVENTION))
    args = parser.parse_args()
    print(pretty(run(args.world) if args.command == "run" else replay(args.world)))
