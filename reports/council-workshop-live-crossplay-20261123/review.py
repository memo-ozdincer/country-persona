"""Verify the live seat assignments and score matched workshop traces."""

from collections import Counter
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]/"research/council_workshop"))
from replay import replay


def read(path):
    return json.loads(path.read_text())


def packet(prompt):
    return json.JSONDecoder().raw_decode(prompt[prompt.index("{"):])[0]


def summarize(directory):
    result = replay(directory)
    settings = read(directory/"settings.json")
    calls = [json.loads(line) for line in (directory/"calls.jsonl").read_text().splitlines()]
    cap = settings["call_cap"]
    allowed = settings["case"]["mandate_game"]["allowed"]
    count = Counter()
    invalid = []
    requests = calls[::2]
    for req, res in zip(requests, calls[1::2], strict=True):
        assert req["event"] == "request" and res["event"] == "response"
        seat = req["country"]
        assert seat == res["country"]
        model = settings.get("seat_models", {}).get(seat, settings["model"])
        assert req.get("model", model) == model
        count[model] += 1
        state = packet(req["prompt"])
        assert set(state["evidence"]) == {seat}
        assert state["private_mandate"]["allowed_packages"] == sorted(allowed[seat])
        if res["answer"]["action"] == "accept":
            public = state["public"]
            current = next(label for label, text in public["options"].items() if text == public["draft"])
            if current not in allowed[seat]:
                invalid.append([seat, current, public["version"]])
    assert result["calls"] == len(requests) <= cap
    return {
        "seat_models": {seat: settings.get("seat_models", {}).get(seat, settings["model"])
                        for seat in settings["countries"]},
        "calls": result["calls"], "speeches": len(result["history"]),
        "fresh_calls": sum(not row["reused"] for row in calls[1::2]),
        "calls_by_model": dict(sorted(count.items())),
        "opening": result["history"][0],
        "out_of_mandate_acceptances": invalid, "exclusions": result["exclusions"],
        **result["mandate_score"],
    }, settings, packet(requests[0]["prompt"])


def compare():
    feasible, a, a_opening = summarize(HERE/"feasible")
    impasse, b, b_opening = summarize(HERE/"impasse")
    keys = ("countries", "model", "seat_models", "turn_cap", "call_cap", "vote", "mode", "codex")
    assert all(a[key] == b[key] for key in keys)
    assert a_opening.pop("private_mandate") != b_opening.pop("private_mandate")
    assert a_opening == b_opening
    assert a["case"]["mandate_game"]["allowed"]["KEN"] == ["assessment", "context"]
    assert b["case"]["mandate_game"]["allowed"]["KEN"] == ["assessment"]
    assert a["case"] | {"mandate_game": b["case"]["mandate_game"]} == b["case"]
    assert a["case"]["mandate_game"]["options"] == b["case"]["mandate_game"]["options"]
    assert {k:v for k,v in a["case"]["mandate_game"]["allowed"].items() if k != "KEN"} == {
        k:v for k,v in b["case"]["mandate_game"]["allowed"].items() if k != "KEN"}
    history = [read(HERE / name / "result.json")["history"] for name in ("feasible", "impasse")]
    shared = 0
    for left, right in zip(*history):
        if any(left[k] != right[k] for k in ("country", "action", "version")):
            break
        shared += 1
    output = {"opening_view_diff": "one private option for KEN",
              "shared_opening_speech_actions": shared, "feasible": feasible, "impasse": impasse}
    extension, longer, _ = summarize(HERE/"feasible-extended")
    assert all(a[key] == longer[key] for key in keys if key != "turn_cap")
    assert longer["case"] == a["case"] and longer["turn_cap"] == a["turn_cap"]+1
    original, continued = (
        [json.loads(line) for line in (HERE / name / "calls.jsonl").read_text().splitlines()]
        for name in ("feasible", "feasible-extended")
    )
    assert len(continued) >= len(original)
    for index, (old, new) in enumerate(zip(original, continued)):
        assert old == (new | {"reused": False} if index % 2 else new)
        if index % 2:
            assert new["reused"]
    output["feasible_extension"] = extension
    return output


if __name__ == "__main__":
    print(json.dumps(compare(), ensure_ascii=False, indent=2))
