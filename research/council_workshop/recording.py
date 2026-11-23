"""Consume a previous decision log in order, matching the full input at each step."""
import json
from pathlib import Path


class Recording:
    def __init__(self, directory: Path, stop_before_schema=None):
        lines = (directory / "calls.jsonl").read_text().splitlines()
        events = []
        for line in lines:
            event = json.loads(line)
            if (stop_before_schema is not None and event.get("event") == "request"
                    and event.get("schema") == stop_before_schema):
                break
            events.append(event)
        self.events = iter(events)

    def take(self, request):
        event = next(self.events, None)
        if event is None:
            return None
        if event != request:
            raise ValueError(f"Saved request differs for {request['country']}")
        response = next(self.events, None)
        if response is None:
            return None  # Interrupted after recording the request.
        if response.get("event") == "error":
            self.require_end()
            return None
        if response.get("event") != "response" or response.get("country") != request["country"]:
            raise ValueError("Saved response does not match its request")
        return response["answer"]

    def require_end(self):
        if next(self.events, None) is not None:
            raise ValueError("Unexpected events after the last decision")


def decision_request(settings, country, prompt, schema):
    request = dict(event="request", country=country, prompt=prompt, schema=schema)
    if "seat_models" in settings:
        request["model"] = settings["seat_models"].get(country, settings["model"])
    return request


def verify_run(directory, simulate):
    settings = json.loads((directory / "settings.json").read_text())
    recorded = Recording(directory)

    def call(country, prompt, schema):
        request = decision_request(settings, country, prompt, schema)
        answer = recorded.take(request)
        if answer is None:
            raise ValueError(f"Missing response for {country}")
        return answer

    limits = {"call_cap": settings["call_cap"]} if "call_cap" in settings else {}
    result = simulate(settings["case"], settings["countries"], settings["mode"],
                      settings["turn_cap"], settings["vote"], call, **limits)
    recorded.require_end()
    if result != json.loads((directory / "result.json").read_text()):
        raise ValueError("Replayed outcome differs from saved result")
    return result


def verify_aborted_run(directory, settings, simulate):
    """Replay a terminal failure and distinguish a rejected reply from a missing reply."""
    records = [json.loads(line) for line in (directory / "calls.jsonl").read_text().splitlines()]
    if not records or records[-1].get("event") != "error":
        raise ValueError(f"No recorded terminal error in {directory}")
    detail = records[-1]["message"]
    recording = Recording(directory)
    last_request = None
    calls = 0

    class UnansweredRequest(Exception):
        pass

    def call(country, prompt, schema):
        nonlocal last_request, calls
        last_request = None
        request = decision_request(settings, country, prompt, schema)
        reply = recording.take(request)
        last_request = request
        calls += 1
        if reply is None:
            raise UnansweredRequest
        return reply

    try:
        simulate(settings["case"], settings["countries"], settings["mode"],
                 settings["turn_cap"], settings["vote"], call, call_cap=settings.get("call_cap"))
    except UnansweredRequest:
        if records[-2] != last_request:
            raise ValueError("Call error did not follow the replayed request") from None
        status = "call_error"
    except (KeyError, ValueError) as error:
        if not (last_request and records[-3] == last_request and str(error) == detail):
            raise ValueError("Recorded protocol error did not reproduce") from error
        if next(recording.events, None) != records[-1]:
            raise ValueError("Unexpected decisions before the recorded protocol error") from error
        status = "protocol_error"
    else:
        raise ValueError("Meeting completed during replay of an aborted run")
    recording.require_end()
    prompt = last_request["prompt"]
    packet, _ = json.JSONDecoder().raw_decode(prompt[prompt.index("{"):])
    return status, detail, calls, packet["public"]
