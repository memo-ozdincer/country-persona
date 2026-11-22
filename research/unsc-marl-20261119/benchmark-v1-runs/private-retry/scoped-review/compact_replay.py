"""Decode exact-length compact replies from the numbered checklist."""
from unittest.mock import patch

import indexed_checklist as indexed
import scoped_review as original

verified_rows = original.rows


def compact_rows():
    for request, response in verified_rows():
        expected = len(request["units"]) + 1
        text = response["text"]
        if len(text) == expected and set(text) <= {"A", "B"}:
            response = {**response, "text": " ".join(text)}
        yield request, response


if __name__ == "__main__":
    folder = indexed.HERE
    with patch.multiple(original, HERE=folder, EVIDENCE=folder / "evidence",
                        plan=indexed.indexed_plan, rows=compact_rows):
        original.emit(original.evaluate())
