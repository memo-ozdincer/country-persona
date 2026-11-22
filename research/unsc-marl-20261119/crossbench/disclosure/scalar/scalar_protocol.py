"""Single-record disclosure format retaining the original public ledger."""
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from protocol import FAMILY, ROOT, FORMAT, family_inputs, script, serialize, summarize
from protocol import admit as admit_lists
from protocol import request as request_lists

SCALAR_FORMAT = (
    'Return only one JSON object with exactly two scalar fields. '
    '"stance" must be "accept", "exclude", or "pass". '
    'For "accept" or "exclude", "option" must be one letter A, B, C, or D. '
    'For "pass", "option" must be null. An exclusion example is {"stance":"exclude","option":"C"}. '
    'Do not use arrays or name more than one option. Report only a truthful claim about your own private condition. '
    'Choose a claim that could help the group establish the outcome.'
)


def request(*args, **kwargs):
    data = request_lists(*args, **kwargs)
    decoded = json.loads(data["messages"][1]["content"])
    assert decoded["task"].startswith(FORMAT)
    decoded["task"] = SCALAR_FORMAT + decoded["task"][len(FORMAT):]
    return {**data, "messages": [data["messages"][0], {"role": "user", "content": serialize(decoded)}]}


def admit(raw, record_id, author, known):
    def no_duplicates(pairs):
        value = dict(pairs)
        if len(value) != len(pairs):
            raise ValueError("Repeated JSON key")
        return value

    try:
        value = json.loads(raw, object_pairs_hook=no_duplicates)
        if not isinstance(value, dict) or set(value) != {"stance", "option"}:
            raise ValueError("Expected stance and option fields")
        stance, option = value["stance"], value["option"]
        converted = {"accepts": [], "excludes": []}
        if stance == "pass" and option is None:
            pass
        elif stance in ("accept", "exclude") and isinstance(option, str) and option in ("A", "B", "C", "D"):
            converted[stance + "s"].append(option)
        else:
            raise ValueError("Invalid stance or option")
    except (ValueError, TypeError):
        return {"kind": "invalid_format", "admitted": None}
    return admit_lists(serialize(converted), record_id, author, known)
