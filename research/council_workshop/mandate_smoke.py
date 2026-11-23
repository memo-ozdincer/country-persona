"""Replay scripted baselines for every opener in the two climate package cases."""

import json
from itertools import product

from meeting import FLOOR, PACKAGE_SPEECH
from run import HERE, simulate


def policy(kind):
    def decide(country, prompt, schema):
        packet = json.JSONDecoder().raw_decode(prompt[prompt.index("{"):])[0]
        if schema is FLOOR:
            return {"action": "request_floor"}
        if schema is not PACKAGE_SPEECH:
            raise ValueError("Unexpected decision schema")
        public = packet["public"]
        action, text = "yield_floor", "Await another delegate's input."
        if kind == "always_accept":
            action, text = "accept", "Accept the current clause."
        elif kind == "always_exit":
            action, text = "walk_away", "End discussion."
        else:
            remaining = public["options"].keys() - public["exclusions"].keys()
            allowed = set(packet["private_mandate"]["allowed_packages"])
            vetoes = sorted(remaining - allowed)
            if vetoes:
                action, text = "rule_out", vetoes[0]
            elif not remaining:
                action, text = "declare_impasse", "All options have verified rejections."
            elif len(remaining) == 1:
                package, = remaining
                if public["draft"] != public["options"][package]:
                    action, text = "propose", package
                elif country not in public["accepted"]:
                    action, text = "accept", "Accept the remaining package."
        return {"action": action, "version": public["version"], "text": text}
    return decide


def run():
    rows = []
    cases = ("feasible", "impasse")
    strategies = ("checked_exchange", "always_accept", "always_exit")
    for world, strategy in product(cases, strategies):
        case = json.loads((HERE / f"climate-packages-{world}.json").read_text())
        seats = list(case["delegations"])
        for start in range(len(seats)):
            order = seats[start:] + seats[:start]
            result = simulate(case, order, "meeting", 20, False, policy(strategy), call_cap=50)
            rows.append({"world": world, "strategy": strategy, "order": order,
                         "calls": result["calls"], "turns": len(result["history"]),
                         "terminal": result["status"], "exclusions": result["exclusions"],
                         **result["mandate_score"]})
    return rows


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
