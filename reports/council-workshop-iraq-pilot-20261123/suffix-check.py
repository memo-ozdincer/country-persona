"""Replay the all-Sol prefix and test two adjacent points to switch policy."""

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "research/council_workshop"))

from held_suite import checked_exchange, metrics
from meeting import FLOOR
from recording import Recording, decision_request
from replay import replay
from run import pretty, simulate


def run_suffix(source, settings, after_speeches):
    recording = Recording(source)
    reused = 0
    switch = None

    def call(seat, prompt, schema):
        nonlocal reused, switch
        packet, _ = json.JSONDecoder().raw_decode(prompt[prompt.index("{"):])
        state = packet["public"]
        speeches = len(state["history"])
        if speeches < after_speeches or (speeches == after_speeches and schema is FLOOR):
            reply = recording.take(decision_request(settings, seat, prompt, schema))
            if reply is None:
                raise ValueError(f"Missing recorded reply before the switch for {seat}")
            reused += 1
            return reply
        if switch is None:
            switch = {"seat": seat, "queue_behind_speaker": state["queue"]}
        return checked_exchange(seat, prompt, schema)

    result = simulate(settings["case"], settings["countries"], settings["mode"], settings["turn_cap"],
                      settings["vote"], call, call_cap=settings["call_cap"])
    return {"after_speeches": after_speeches, "reused_calls": reused, "switch": switch,
            "scripted_speeches": result["history"][after_speeches:], **metrics(result, settings["case"])}


if __name__ == "__main__":
    source = HERE / "all-sol"
    replay(source)
    settings = json.loads((source / "settings.json").read_text())
    print(pretty([run_suffix(source, settings, after_speeches) for after_speeches in (12, 13)]))
