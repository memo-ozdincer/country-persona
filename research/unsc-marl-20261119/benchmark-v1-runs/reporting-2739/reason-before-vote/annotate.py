"""Record the assistant's exact-span review against the unchanged 2739 rubric."""

import json

from experiment import HERE, previous
from scored_replay import scorer

REASONS = {
    "none": "The writer abstains when no statements arrive.",
    "sponsors": "The writer abstains with only the sponsors' position.",
    "algeria": "The writer abstains with only Algeria's position.",
    "sponsors-first": (
        "The comparison states that Algeria valued the reports and that the sponsors valued accurate information. "
        "It leaves the shared purpose of keeping the Council informed implicit."
    ),
    "algeria-first": (
        "The line compares the vote and implementation concerns with the sponsors' reporting purpose. "
        "It omits Algeria's stated reason for valuing the reports in that comparison."
    ),
    "action-first": (
        "The line compares Algeria's vote explanation with the adopted action. "
        "The sponsors' stated reason is absent."
    ),
    "action-second": (
        "The line juxtaposes Algeria's vote explanation and the adopted reporting extension. "
        "The sponsors' stated reason is absent."
    ),
}


def marks():
    outputs = previous.base.read(HERE / "verified.json")["outputs"]
    result = {}
    for name, receipts in previous.ORDERS.items():
        text = outputs[name]["text"]
        abstained = text == "NONE"
        assert abstained == (len(receipts) < 2)
        result[name] = {
            "overlap": {
                "id": "bounded-overlap", "status": "unmet",
                "source": [] if abstained else scorer.citations(*receipts),
                "response": "" if abstained else text,
                "reason": REASONS[name],
            },
            "guard": {
                "status": "clear", "source": [], "response": "",
                "reason": "The appended comparison, where present, stays within the attributed source evidence.",
            },
        }
    return result


if __name__ == "__main__":
    print(json.dumps(marks(), ensure_ascii=False, indent=2))
