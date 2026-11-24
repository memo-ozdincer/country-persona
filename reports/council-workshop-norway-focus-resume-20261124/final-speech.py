"""Check every distinct legal action at the interrupted tenth speech."""

import json

from paired import FOLLOWUP, HERE, plan, read
from meeting import PACKAGE_SPEECH
from recording import Recording, decision_request, simulation_options
from run import pretty, simulate
from train_mandates import candidates


def audit():
    design = plan(FOLLOWUP, 25, 9, PACKAGE_SPEECH)
    assert design == read(HERE / "final-plan.json")
    settings = read(FOLLOWUP / "settings.json")
    request = design["retry"]
    prompt = request["prompt"]
    packet, _ = json.JSONDecoder().raw_decode(prompt[prompt.index("{"):])
    seat, public = request["country"], packet["public"]
    assert len(public["history"]) == settings["turn_cap"] - 1
    allowed = set(packet["private_mandate"]["allowed_packages"])
    actions, selected = candidates(public, seat, allowed)
    actions += [("ask", selected), ("reply", selected)]
    rows = []
    for action, package in actions:
        prefix = Recording(FOLLOWUP)
        injected = []

        def respond(country, prompt, schema):
            current = decision_request(settings, country, prompt, schema)
            reply = prefix.take(current)
            if reply is not None:
                return reply
            assert not injected and current == request
            injected.append(current)
            return {"action": action, "version": public["version"],
                    "text": package if action in ("rule_out", "propose") else action}

        result = simulate(settings["case"], settings["countries"], settings["mode"],
                          settings["turn_cap"], settings["vote"], respond, **simulation_options(settings))
        assert len(injected) == 1 and result["calls"] == 25 and len(result["history"]) == 10
        rows.append({"action": action, "package": package if action in ("rule_out", "propose") else None,
                     "status": result["status"], "reward": result["mandate_score"]["reward"],
                     "exclusion_count": len(result["exclusions"])})
    missing = sorted(public["options"].keys() - public["exclusions"].keys())
    return {"seat": seat, "call": 25, "speech": 10, "missing_exclusions": missing,
            "best_possible_reward": max(row["reward"] for row in rows), "actions": rows}


if __name__ == "__main__":
    print(pretty(audit()))
