"""Replay one shared policy with six speeches and the original call cap."""

from copy import deepcopy

from fork import CALL_CAP, FLOOR, HERE, ORDER, metrics, packet, pretty, read, simulate


def shared_policy(country, prompt, schema):
    view = packet(prompt)
    history = view["public"]["history"]
    turn = len(history)
    if turn < 3:
        seat = ORDER[turn]
    elif history[2]["action"] == "accept":
        seat = ["GHA", "CHN"][turn - 3]
    else:
        seat = ["CHN", "NOR", "GHA"][turn - 3]
    if schema is FLOOR:
        return {"action": "request_floor" if country == seat else "pass"}

    assert country == seat
    if turn == 0:
        action, text = "rule_out", "review"
    elif turn == 1:
        action, text = "propose", "briefing"
    elif turn == 2:
        allowed = view["private_mandate"]["allowed_packages"]
        action, text = ("accept", "Accept briefing.") if "briefing" in allowed else ("rule_out", "briefing")
    elif history[2]["action"] == "accept":
        action, text = "accept", "Accept briefing."
    else:
        action, text = [("rule_out", "coastal"), ("rule_out", "regional"),
                        ("declare_impasse", "All packages have checked exclusions.")][turn - 3]
    return {"action": action, "version": view["public"]["version"], "text": text}


if __name__ == "__main__":
    outcomes = {}
    for world, original in read(HERE / "fork.json")["cases"].items():
        case = deepcopy(original)
        case["brief"] = case["brief"].replace("five speaking turns", "six speaking turns")
        assert case["brief"] != original["brief"]
        result = simulate(case, ORDER, "meeting", 6, False, shared_policy, call_cap=CALL_CAP)
        assert result["mandate_score"]["reward"] == 1
        outcomes[world] = {**metrics(result, case), "history": result["history"]}
    print(pretty({"speech_cap": 6, "call_cap": CALL_CAP, "shared_policy_success": 1.0, "worlds": outcomes}))
