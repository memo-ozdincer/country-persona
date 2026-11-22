"""Record exact-span assistant grades for the matched chair outputs."""
import json

from readout import scorer
from study_driver import HERE, VIEWS, read

REASONS = {
    "quotes/algeria-first": (
        "The sentence assigns each stated purpose correctly, but juxtaposes them using 'whereas'. "
        "It does not say that informing Council deliberations is the purpose the delegations share."
    ),
    "quotes/action-first": (
        "Only Algeria supplies a stated purpose. The public Council action does not supply the "
        "co-sponsors' reason, so calling this a shared purpose overstates the evidence."
    ),
    "direct/action-second": (
        "The line relates Algeria's abstention to the adopted text. "
        "It supplies no sponsor statement or shared purpose."
    ),
    "quotes/action-second": (
        "The line states Algeria's vote reason and its reason for valuing the reports. "
        "It supplies no sponsor statement or shared purpose."
    ),
}


def marks():
    replies = read(HERE / "verified.json")["chair"]
    annotated = {}
    for key, reply in replies.items():
        view = key.split("/")[-1]
        text = reply["text"]
        is_none = text == "NONE"
        fault = key == "quotes/action-first"
        assert is_none == (key not in REASONS)
        evidence = scorer.citations(*VIEWS[view])
        annotated[key] = {
            "overlap": {
                "id": "bounded-overlap", "status": "unmet",
                "source": [] if is_none else evidence, "response": "" if is_none else text,
                "reason": "The writer abstains." if is_none else REASONS[key],
            },
            "guard": {
                "status": "failed" if fault else "clear",
                "source": evidence if fault else [],
                "response": "a shared practical reason" if fault else "",
                "reason": REASONS[key] if fault else "All retained assertions are supported by the visible evidence.",
            },
        }
    return annotated


if __name__ == "__main__":
    print(json.dumps(marks(), ensure_ascii=False, indent=2))
