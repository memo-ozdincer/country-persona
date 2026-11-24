"""Test the changed final Gulf speech after skipping a real request to speak."""

import argparse
import json

from audit import HERE, ROOT, UnrecordedDecision, compare, pretty
from codex_runner import CodexRunner
from meeting import PACKAGE_SPEECH


SOURCE = ROOT / "reports/council-workshop-held-pilot-20261123/sol-with-astra-norway"
LOG = HERE / "gulf-live.jsonl"


def read(path):
    return json.loads(path.read_text())


def plan(settings):
    design = {}

    def capture(request, old):
        old_request, old_reply = old
        assert request["country"] == old_request["country"] == "GHA"
        assert request["model"] == old_request["model"] == settings["model"] == "gpt-6.1-sol"
        assert request["schema"] == old_request["schema"] == PACKAGE_SPEECH
        assert old_reply["answer"]["action"] == "declare_impasse"
        public_queue = '"queue": [\n      "CHN"\n    ]'
        assert old_request["prompt"].count(public_queue) == 1
        assert request["prompt"] == old_request["prompt"].replace(public_queue, '"queue": []')
        design.update(request=request, original_reply=old_reply["answer"], changed_field="public.queue")
        raise UnrecordedDecision

    row = compare(SOURCE, settings, capture)
    assert row["original"]["speeches"] == settings["turn_cap"] == 10
    assert row["reused_calls"] == 22 and row["first_unrecorded_decision"]["variant_call"] == 23
    assert row["bypassed_polls"] == [{"original_call": 23, "seat": "CHN", "action": "request_floor"},
                                    {"original_call": 24, "seat": "NOR", "action": "pass"}]
    return row | design


def continuation(settings, design, answer):
    fresh = 0

    def respond(request, old):
        nonlocal fresh
        assert fresh == 0 and request == design["request"] and old[1]["answer"] == design["original_reply"]
        fresh += 1
        return answer(request)

    row = compare(SOURCE, settings, respond)
    assert fresh == 1 and row["variant"]["calls"] == 23 and row["variant"]["speeches"] == 10
    return row


def run(settings, design):
    runner = CodexRunner(settings["model"], timeout=settings["call_timeout"])
    with LOG.open("x") as log:
        def answer(request):
            print(json.dumps(request, ensure_ascii=False), file=log, flush=True)
            try:
                reply = runner(request["prompt"], request["schema"])
            except (OSError, TimeoutError, ValueError, RuntimeError) as error:
                print(json.dumps({"event": "error", "message": str(error)}), file=log, flush=True)
                raise
            print(json.dumps({"event": "response", "answer": reply}, ensure_ascii=False), file=log, flush=True)
            return reply

        return continuation(settings, design, answer)


def replay(settings, design):
    saved_request, saved_reply = map(json.loads, LOG.read_text().splitlines())

    def answer(request):
        assert saved_request == request and saved_reply["event"] == "response"
        return saved_reply["answer"]

    return continuation(settings, design, answer)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "live", "replay"))
    args = parser.parse_args()
    settings = read(SOURCE / "settings.json")
    design = plan(settings)
    if args.command == "plan":
        print(pretty(design))
    else:
        assert design == read(HERE / "gulf-plan.json")
        print(pretty((run if args.command == "live" else replay)(settings, design)))
