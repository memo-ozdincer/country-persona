"""Audit the semantic sufficiency of each source witness."""

import json

from collect_witnesses import HERE, read

SUFFICIENCY = {
    "reform/uk-explanation": (False, "The output expresses the timing objection but changes the source apostrophe and adds an ellipsis."),
    "reform/uk-negotiations": (False, "The output expresses the timing objection but changes the source apostrophe and adds an ellipsis."),
    "afghanistan/russia-full": (
        False, "The quote exactly gives the condition for support. The antecedent of 'his decision' is outside the quote, so it does not identify the appointment standalone."
    ),
    "afghanistan/russia-consultation-only": (
        False, "The exact span makes consultation and taking account of views important. It supplies no requirement of agreement for the speaker's support."
    ),
    "afghanistan/china-full": (
        False, "The span discussed communication and consultation, without making agreement a condition of support. It also changes the source apostrophe."
    ),
    "afghanistan/russia-agreement-deletion": (
        False, "The exact span says 'fundamental condition' without identifying a condition of agreement or a commitment to withdraw support."
    ),
}


def marks():
    archive = read(HERE / "verified.json")["cases"]
    assert set(SUFFICIENCY) == {k for k, row in archive.items() if row["extraction"]["text"] != "NONE"}
    return {
        key: {
            "sufficient": SUFFICIENCY.get(key, (False, "No source excerpt is offered."))[0],
            "reason": SUFFICIENCY.get(key, (False, "No source excerpt is offered."))[1],
            "sufficient_with_full_source": key == "afghanistan/russia-full",
        }
        for key in archive
    }


if __name__ == "__main__":
    print(json.dumps(marks(), ensure_ascii=False, indent=2))
