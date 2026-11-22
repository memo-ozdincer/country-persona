"""Evaluate a separate post hoc normalization of literal numeric IDs."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import evaluate_somalia as q

original = q.normalize
HERE = Path(__file__).resolve().parent


def normalize(row, menus):
    ids, status = original(row, menus)
    response = row["response"]
    if ids or response["termination"] != "complete":
        return ids, status
    try:
        items = json.loads(response["text"])
    except json.JSONDecodeError:
        return ids, status
    if not isinstance(items, list) or not items or not all(type(i) is int for i in items):
        return ids, status
    normalized = row | {"response": response | {"text": json.dumps([str(i) for i in items])}}
    chosen, accepted = original(normalized, menus)
    return (chosen, "normalized_literal_ids") if chosen else (ids, status)


def grade():
    for candidate in ([True], [9.0], [9, "2"], [99], [9, 9]):
        fixture = {"part": "china", "response": {"text": json.dumps(candidate), "termination": "complete"}}
        assert normalize(fixture, q.n.read(q.t.SOURCE)["menus"])[0] == []
    with patch.object(q, "normalize", normalize):
        return q.grade()


def replay():
    grades = HERE / "numeric-grades.json"
    measured = q.replay(q.n.read(grades))
    del measured["sha256"]["grades.json"]
    for path in (grades, Path(__file__), HERE / "numeric-format.md"):
        measured["sha256"][path.name] = sha256(path.read_bytes()).hexdigest()
    return measured


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("grades", "replay"))
    q.e.emit(grade() if parser.parse_args().mode == "grades" else replay())
