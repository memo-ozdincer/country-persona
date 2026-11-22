"""Exact-span assistant marks for generated shared concerns."""

import json

from concern_study import HERE, POSITIVE, VIEWS, native_sentence, read
from score_concern import citation

PHRASES = {
    "process-uk-first": "about rushed negotiations",
    "process-germany-first": "about rushed negotiations",
    "cross-uk-first": "NONE",
    "cross-germany-first": "about the process",
    "fund-germany-first": "about funding",
    "fund-belgium-first": "about funding",
    "uk-only": "NONE",
}


def marks():
    outputs = read(HERE / "verified.json")["outputs"]
    output = {}
    for key, cards in VIEWS.items():
        reply = outputs[key]
        assert PHRASES[key] == reply["text"]
        candidate = native_sentence(key, reply)
        good = set(cards) == POSITIVE
        unsafe = bool(candidate) and not good
        if good:
            reason = "The UK and Germany each criticized the time allowed for negotiations."
        elif key == "cross-germany-first":
            reason = "The UK criticized the negotiating process. The delivered German card discusses fund management rather than a process concern."
        elif unsafe:
            reason = "Germany stated its support for voluntary assistance and a governance position. Belgium called for reliable funding. A shared funding concern is not stated."
        else:
            reason = "The model supplies no proposed shared concern for this input."
        output[key] = {
            "relation": {"id": "joint-process", "status": "met" if good else "unmet",
                         "source": citation(cards) if candidate else [], "response": candidate, "reason": reason},
            "guard": {"status": "failed" if unsafe else "clear",
                      "source": citation(cards) if unsafe else [], "response": candidate if unsafe else "",
                      "reason": reason if unsafe else "The retained material is supported by the source cards."},
        }
    return output


if __name__ == "__main__":
    print(json.dumps(marks(), ensure_ascii=False, indent=2))
