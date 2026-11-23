"""Replay a scripted speaker behind the same opening and assigned floor."""

import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]/"research/council_workshop"))
from floor_diagnostic import archived, scheduled_floor
from local_baseline import WORLDS
from mandate_smoke import policy
from meeting import FLOOR
from run import simulate


def run():
    rows = {}
    for world in WORLDS:
        settings, first, _ = archived(world)
        script = policy("checked_exchange")
        opening_used = False

        def call(country, prompt, schema):
            nonlocal opening_used
            if not opening_used:
                assert first[0][0]["country"] == country and first[0][0]["prompt"] == prompt
                opening_used = True
                return first[0][1]["answer"]
            if schema == FLOOR:
                return scheduled_floor(settings, country, prompt)
            return script(country, prompt, schema)

        result = simulate(settings["case"], settings["countries"], "meeting", settings["turn_cap"],
                          False, call, settings["call_cap"])
        rows[world] = {"turns":len(result["history"]), "decision_slots":result["calls"],
                       "status":result["status"], "exclusions":result["exclusions"],
                       **result["mandate_score"]}
    return rows


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
