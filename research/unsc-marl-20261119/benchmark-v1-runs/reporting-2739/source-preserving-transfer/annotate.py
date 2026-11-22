"""Exact-span assistant marks for the seven optional comparison outputs."""
import json

from score import citations
from study import HERE, ORDERS, base

RATIONALES = {
    "none": "With no delivered statement, the model abstains.",
    "sponsors": "The model abstains with only the sponsors' statement.",
    "algeria": "The model abstains with only Algeria's statement.",
    "sponsors-first": (
        "The comparison juxtaposes the sponsors' support and Algeria's abstention. "
        "It never ties Algeria's stated value for continued reporting to the sponsors' rationale."
    ),
    "algeria-first": (
        "The sentence repeats the delegation's abstention and the sponsors' support. "
        "The shared reason to keep the Council informed remains in separate, parallel passages."
    ),
    "action-first": (
        "The action text and Algeria's statement support a contrast between the adopted action "
        "and the abstention, but supply no sponsor reporting rationale to connect."
    ),
    "action-second": "The chair abstains when it receives Algeria's position and the public action only.",
}


def marks():
    raw = base.read(HERE / "verified.json")["outputs"]
    return {
        name: {
            "overlap": {
                "id": "bounded-overlap", "status": "unmet",
                "source": [] if raw[name]["text"] == "NONE" else citations(*receipts),
                "response": "" if raw[name]["text"] == "NONE" else raw[name]["text"],
                "reason": RATIONALES[name],
            },
            "guard": {
                "status": "clear", "source": [], "response": "",
                "reason": "The fixed facts and any appended claims are supported by the visible evidence.",
            },
        } for name, receipts in ORDERS.items()
    }


if __name__ == "__main__":
    print(json.dumps(marks(), ensure_ascii=False, indent=2))
