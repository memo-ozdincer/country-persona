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
