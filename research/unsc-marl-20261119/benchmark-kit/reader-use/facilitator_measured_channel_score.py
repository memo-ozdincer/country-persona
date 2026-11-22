"""Audit a blind candidate against three packet-local source requirements."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import facilitator_measured_channel_replies as study


def alias(key):
    return sha256(f"2719-channel-reply:{key}".encode()).hexdigest()[:8]


def blind(rows):
    cards = study.cards()
    return dict(sorted((alias(key), {"reply": value["output"], "ended": value["ended"],
                                     "required": cards[int(key[-1]) - 1]["required"],
                                     "source": cards[int(key[-1]) - 1]["source"]})
                       for key, value in rows.items()))


def score(rows, marks):
    matrix = [[1, 0, 0, 0] for _ in range(4)]
    assert set(marks) == {alias(key) for key in rows}
    data = {}
    for key, row in sorted(rows.items()):
        q, c = map(int, key.split("/"))
        mark = marks[alias(key)]
        assert len(mark["required"]) == 3
        words = len(row["output"].split())
        spans = [w for term in mark["required"] for w in term] + mark["errors"]
        assert all(w and w in row["output"] for w in spans)
        okay = row["ended"] and words <= 52 and all(mark["required"]) and not mark["errors"]
        matrix[q][c] = int(okay)
        data[key] = {"passed": okay, "words": words, "ended": row["ended"], "assessment": mark,
                     "reply": row["output"], "input_tokens": len(row["input_ids"]),
                     "output_tokens": len(row["output_ids"])}
    return {"matrix": matrix, "replies": data, "passed_replies": sum(x["passed"] for x in data.values())}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("blind", "score"))
    p.add_argument("directory", type=Path)
    arg = p.parse_args()
    rows = study.verify(arg.directory)
    output = blind(rows) if arg.mode == "blind" else score(rows, json.loads((arg.directory / "review.json").read_text()))
    print(json.dumps(output, ensure_ascii=False, indent=2))
