"""Enumerate which frozen actions the language responder guide can represent."""
import json

import numpy as np

import routing_climate_live_exchange as live


def compare():
    transfer = live.transfer
    route = transfer.route
    (ask, send, trained_reply), swap, weight = max(live.read(live.channel.PLAN)["plans"]["learned"],
                                                  key=lambda row: row[2])
    ask, send, trained_reply = map(np.asarray, (ask, send, trained_reply))
    guide_reply = np.empty_like(trained_reply)
    for right in range(8):
        available = np.flatnonzero(route.SEND[right, 1:]) + 1
        default = int(available[0]) if available.size else 0
        guide_reply[right] = [q if q in available else default for q in route.ACTIONS]
    trained, guide = (ask, send, trained_reply), (ask, send, guide_reply)
    assert np.array_equal(trained_reply[:, 0], guide_reply[:, 0])
    mismatch = trained_reply[:, ask].T != guide_reply[:, ask].T
    differences = [{"requester_mask": int(left), "responder_mask": int(right), "query": int(ask[left]),
                    "sent": int(send[left]), "trained_reply": int(trained_reply[right, ask[left]]),
                    "literal_guide_reply": int(guide_reply[right, ask[left]])}
                   for left, right in np.argwhere(mismatch)]
    priors, _, _ = transfer.original.selections()
    payoff = transfer.payoff(transfer.task())
    values = {}
    for name, p in priors.items():
        prior = p.T if swap else p
        value = {label: route.evaluate(policy, prior, payoff, route.TRAIN_LOSS)["net"]
                 for label, policy in (("trained", trained), ("literal_guide", guide))}
        values[name] = {**value, "net_loss_under_literal_guide": value["trained"] - value["literal_guide"],
                        "probability_of_a_different_reply": float(prior[mismatch].sum() * (1 - route.TRAIN_LOSS))}
    return {"scope": "Exact policy replay on the announced rubric, assuming perfect execution of literal instructions. "
                     "Differences forecast a possible implementation gap in the selected component. "
                     "They do not estimate language output quality.",
            "component_weight": weight, "worlds": 64, "different_worlds": differences, "priors": values}


if __name__ == "__main__":
    print(json.dumps(compare(), indent=2))
