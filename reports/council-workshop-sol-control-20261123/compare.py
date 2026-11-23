"""Replay the matched live Sol and mixed-roster controls offline."""

from collections import Counter
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
MIXED = HERE.with_name("council-workshop-live-crossplay-20261123")
sys.path.insert(0, str(HERE.parents[1] / "research/council_workshop"))
from mandate_smoke import policy
from replay import replay
from run import simulate


def endpoint(result):
    return {
        "status": result["status"],
        "speeches": [[row["country"], row["action"], row["resulting_version"]] for row in result["history"]],
        "calls": result["calls"],
        "signatures": result["accepted"],
        "exclusions": result["exclusions"],
        "queue": result["queue"],
        **result["mandate_score"],
    }


def decision_log(directory):
    return [json.loads(line) for line in (directory / "calls.jsonl").read_text().splitlines()]


def summarize(directory, original=None):
    result = replay(directory)
    calls = decision_log(directory)
    prefix = decision_log(original) if original is not None else []
    assert len(calls) >= len(prefix)
    for index, old in enumerate(prefix):
        expected = old | {"reused": True} if index % 2 else old
        assert calls[index] == expected
    decisions = Counter()
    incompatible_signatures = []
    for index, (request, reply) in enumerate(zip(calls[::2], calls[1::2], strict=True)):
        assert reply["reused"] == (2 * index < len(prefix))
        action = reply["answer"]["action"]
        decisions[action] += 1
        if action == "accept":
            prompt = request["prompt"]
            view, _ = json.JSONDecoder().raw_decode(prompt[prompt.index("{"):])
            public = view["public"]
            package = next(label for label, text in public["options"].items() if text == public["draft"])
            if package not in view["private_mandate"]["allowed_packages"]:
                incompatible_signatures.append([request["country"], package, public["version"]])
    assert sum(decisions.values()) == result["calls"]
    return {
        **endpoint(result),
        "fresh_calls": result["calls"] - len(prefix) // 2,
        "actions": dict(sorted(decisions.items())),
        "incompatible_signatures": incompatible_signatures,
    }


def check_settings(mixed, all_sol, turn_cap):
    mixed_settings, sol_settings = (
        json.loads((directory / "settings.json").read_text()) for directory in (mixed, all_sol)
    )
    assert mixed_settings.pop("seat_models") == {"KEN": "gpt-6-astra"}
    assert sol_settings.pop("seat_models", {}) == {}
    assert mixed_settings["model"] == "gpt-6.1-sol"
    for directory, settings in ((mixed, mixed_settings), (all_sol, sol_settings)):
        settings.pop("started")
        parent = settings.pop("extended_from", None)
        if turn_cap == 10:
            assert (HERE.parents[1] / parent).resolve() == directory.with_name("feasible")
        else:
            assert parent is None
    assert mixed_settings == sol_settings
    assert sol_settings["countries"] == ["KEN", "GBR", "IND", "FRA", "BRA"]
    assert (sol_settings["turn_cap"], sol_settings["call_cap"], sol_settings["vote"]) == (turn_cap, 50, False)
    return sol_settings


def compare():
    pairs = {}
    for case in ("feasible", "impasse"):
        mixed, all_sol = MIXED / case, HERE / case
        sol_settings = check_settings(mixed, all_sol, 9)
        scripted = simulate(
            sol_settings["case"], sol_settings["countries"], sol_settings["mode"],
            sol_settings["turn_cap"], sol_settings["vote"], policy("checked_exchange"),
            call_cap=sol_settings["call_cap"],
        )
        pairs[case] = {"mixed": summarize(mixed), "all_sol": summarize(all_sol), "checked_exchange": endpoint(scripted)}
        if case == "feasible":
            extended = MIXED / "feasible-extended", HERE / "feasible-extended"
            assert check_settings(*extended, 10) == sol_settings | {"turn_cap": 10}
            pairs["feasible_continuations"] = {
                "mixed": summarize(extended[0], mixed),
                "all_sol": summarize(extended[1], all_sol),
            }
    return pairs


if __name__ == "__main__":
    print(json.dumps(compare(), ensure_ascii=False, indent=2))
