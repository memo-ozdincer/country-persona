"""Bounded authored control for publishing one scope constraint per delegate."""
from itertools import product
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from decision_ledger import readout, truthful_disclosure


def evaluate(model_scopes=None):
    case = json.loads((HERE / "case.json").read_text())
    result = json.loads((HERE / "evidence/metrics.json").read_text())
    options = [opt["id"] for opt in case["options"]]
    roles = case["roles"]
    clauses = {
        "japan": ("you cannot approve a broadened first stage", {"broad"}),
        "china-overlap": ("Accept a text only if broader issues are included immediately or explicitly assigned to a second stage", {"focused"}),
        "china-impasse": ("Broader issues must be included in the first stage", {"focused", "staged"}),
    }
    outcomes = {}
    for china in ("china-overlap", "china-impasse"):
        cards = ("japan", china)
        decisions = [{option: result["decisions"][f"{card}/{option}"] for option in options}
                     for card in cards]
        truth = [{option for option, row in local.items() if row["expected"]} for local in decisions]
        for opening in product(*(sorted(menu) for menu in truth)):
            messages, events = [], []

            def publish(actor, accepts, excludes, kind, slot, quote=None):
                claim = {"id": f"claim-{len(messages)+1}", "role": roles[actor],
                         "accepts": accepts, "excludes": excludes}
                event = {"type": kind, "slot": slot, "role": roles[actor], "claim": claim}
                if quote:
                    event["source_quote"] = quote
                event["status"] = "admitted" if truthful_disclosure(claim, truth[actor]) else "rejected"
                events.append(event)
                if event["status"] == "admitted":
                    messages.append(claim)

            def public():
                return readout(options, roles, messages)

            for actor, option in enumerate(opening):
                if decisions[actor][option]["sign"] is True:
                    publish(actor, [option], [], "opening", actor - 2)
                else:
                    events.append({"type": "opening", "slot": actor - 2, "role": roles[actor],
                                   "status": "unknown", "option": option})
            slot = 0
            if public()["state"] == "UNRESOLVED":
                for actor, card in enumerate(cards):
                    if model_scopes is None:
                        quote, scopes = clauses[card]
                        check_type = "authored_scope_check"
                    else:
                        quote, scopes = case["cards"][card], model_scopes[card]
                        check_type = "model_scope_check"
                    assert quote in case["cards"][card]
                    excluded = [option["id"] for option in case["options"] if option["scope"] in scopes]
                    events.append({"type": check_type, "slot": slot, "role": roles[actor],
                                   "source_quote": quote, "excluded_scopes": sorted(scopes)})
                    if excluded or model_scopes is None:
                        publish(actor, [], excluded, "scope_disclosure", slot + 1, quote)
                    else:
                        events.append({"type": "pass", "slot": slot + 1, "role": roles[actor]})
                    slot += 2
            actor = 1
            while slot < 8 and public()["state"] == "UNRESOLVED":
                public_state = public()
                own = {opt for message in messages if message["role"] == roles[actor] for opt in message["accepts"]}
                peer = {opt for message in messages if message["role"] != roles[actor] for opt in message["accepts"]}
                available = [option for option in public_state["unresolved_options"]
                             if option not in own and decisions[actor][option]["sign"] is True]
                if available:
                    chosen = min(available, key=lambda option: (option not in peer, option))
                    publish(actor, [chosen], [], "package_disclosure", slot)
                else:
                    events.append({"type": "pass", "slot": slot, "role": roles[actor]})
                actor = 1 - actor
                slot += 1
            outcomes[f"{china}/{''.join(opening)}"] = {"public": public(), "slots": slot, "events": events}
    scope = ("Retrospective scripted control. Authored source interpretation and multi-package scope disclosures. The public ledger sees admitted claims only."
             if model_scopes is None else
             "Scripted clause routing with frozen model projections and authored disclosure validation.")
    return {"scope": scope, "paths": outcomes}


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
