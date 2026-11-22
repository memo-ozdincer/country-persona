"""Assistant review of the optional comparisons against the locked case rubric."""
import json

from study import CARDS, HERE, ORDERS, read


def marks():
    replies = read(HERE / "verified.json")["outputs"]
    decisions = {
        "none": ("unmet", "No sources for a comparison were delivered."),
        "safeguards": ("unmet", "Only the adopted safeguards were delivered."),
        "india": ("unmet", "Only India's position was delivered."),
        "safeguards-first": (
            "unmet",
            "The added line explains India's reasons but does not explicitly compare the monitoring the Council adopted with the stronger oversight India sought.",
        ),
        "india-first": (
            "met",
            "The added line uses 'while' to connect the adopted monitoring role to India's assessment. The immediately preceding fixed text identifies India's specific desired safeguards and the committee.",
        ),
    }
    output = {}
    for name, receipts in ORDERS.items():
        status, reason = decisions[name]
        text = replies[name]["text"]
        abstention = name not in ("safeguards-first", "india-first")
        assert (text == "NONE") == abstention
        relation = {
            "id": "relation", "status": status, "response": "" if abstention else text,
            "source": [] if abstention else [{"block": src, "quote": CARDS[src]} for src in sorted(receipts)],
            "reason": reason,
        }
        if abstention:
            guard_reason = "The writer abstains and the remaining fixed text uses only the visible cards."
        elif name == "safeguards-first":
            guard_reason = "The wording limits the shortfall to the oversight India deemed necessary, preserving India's attribution."
        else:
            guard_reason = "The national judgment, regime-specific period and existence of adopted monitoring are supported by the cards."
        output[name] = {"relation": relation, "guard": {
            "status": "clear", "response": "", "source": [], "reason": guard_reason,
        }}
    return output


if __name__ == "__main__":
    print(json.dumps(marks(), ensure_ascii=False, indent=2))
