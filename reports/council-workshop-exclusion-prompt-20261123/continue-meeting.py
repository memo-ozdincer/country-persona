"""Continue the archived Iraq prefix with one prompted action and fresh live replies."""

import argparse
import json

from probe import BASELINES, HERE, CodexRunner, grade, plan, read, source_inputs
from held_suite import metrics
from recording import Recording, decision_request
from run import pretty, simulate


def continuation(call_live):
    inputs = source_inputs()
    settings, original, _ = inputs["iraq"]
    trials = read(HERE / "plan.json")
    assert trials == plan(inputs)
    trial = trials["iraq-priority"]
    intervention = read(HERE / "iraq-priority.json")["answer"]
    assert grade(trial, intervention, settings)["target_met"]
    prior = Recording(HERE.parent / BASELINES["iraq"][0])
    reused_calls = 0
    switched = False
    new_calls = 0

    def call(country, prompt, schema):
        nonlocal reused_calls, switched, new_calls
        request = decision_request(settings, country, prompt, schema)
        if not switched:
            reply = prior.take(request)
            if reply is None:
                raise ValueError("Saved discussion ended before the prompted turn")
            if request != original:
                reused_calls += 1
                return reply
            switched = True
            return intervention
        new_calls += 1
        return call_live(request)

    result = simulate(settings["case"], settings["countries"], settings["mode"], settings["turn_cap"],
                      settings["vote"], call, call_cap=settings["call_cap"])
    assert switched and result["calls"] == reused_calls + 1 + new_calls
    return {"archived_calls_reused": reused_calls, "prompted_choice": intervention,
            "fresh_standard_calls": new_calls, "continued_speeches": result["history"][12:],
            **metrics(result, settings["case"])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("run", "replay"))
    args = parser.parse_args()
    log = HERE / "continuation.jsonl"
    if args.command == "run":
        runner = CodexRunner("gpt-6.1-sol", timeout=90)
        with log.open("x") as handle:
            def record(request):
                handle.write(json.dumps(request, ensure_ascii=False) + "\n")
                handle.flush()
                try:
                    answer = runner(request["prompt"], request["schema"])
                except (OSError, TimeoutError, ValueError, RuntimeError) as error:
                    handle.write(json.dumps({"event": "error", "message": str(error)}) + "\n")
                    raise
                handle.write(json.dumps({"event": "response", "answer": answer}, ensure_ascii=False) + "\n")
                handle.flush()
                return answer

            summary = continuation(record)
        with (HERE / "continuation-result.json").open("x") as handle:
            handle.write(pretty(summary) + "\n")
    else:
        events = iter(map(json.loads, log.read_text().splitlines()))

        def recorded(request):
            assert next(events) == request
            response = next(events)
            assert response["event"] == "response"
            return response["answer"]

        summary = continuation(recorded)
        assert next(events, None) is None
        assert summary == read(HERE / "continuation-result.json")
    print(pretty(summary))


if __name__ == "__main__":
    main()
