"""Audit and score the source-bound writer across all matched receipt masks."""
import argparse
from itertools import product
import json
from unittest.mock import patch

import bound_writer as b
import read_native as r

n, e = b.n, b.e


def calls():
    current = b.plan()
    assert current == n.read(b.HERE / "plan.json")
    rows = n.lines(b.OUT / "calls.jsonl")
    assert [{k: row[k] for k in ("part", "request")} for row in rows] == current["requests"]
    return rows


def fragments():
    rows = {}
    for row in calls():
        role = row["part"]
        source = json.loads(row["request"]["messages"][-1]["content"]).get("source")
        rows[role] = b.admit(role, row["response"], source)
    return rows


def structure_check():
    response = {"termination": "complete", "text": json.dumps(
        {"summary": "Desk supported the mission.", "mission_support_quote": "supported it",
         "host_concerns": {"assessment": "some", "quote": "some concerns"}})}
    status = b.admit("Desk", response, "Desk supported it and mentioned some concerns.")
    assert status["mission_support_quote"] and status["host_concerns"]
    dropped = b.admit("Desk", response, "Desk reconsidered.")
    assert set(dropped["issues"]) == {"invalid_mission_quote", "invalid_host_quote"}
    assert not dropped["mission_support_quote"] and dropped["host_concerns"] is None
    assert not b.admit("Other", response, "Desk supported it.")["summary"]
    assert not b.admit("Desk", response | {"termination": "cap"}, "Desk supported it.")["summary"]
    def item(text, assessment):
        return {"summary": text, "mission_support_quote": "support",
                "host_concerns": {"assessment": assessment}}
    fixture = {"public": {"summary": "Public."},
               "Brazil": item("Brazil canary.", "some"),
               "China": item("China canary.", "insufficient"),
               "Russia": {"summary": "Russia canary.", "mission_support_quote": "support", "host_concerns": None}}
    for bits in product((0, 1), repeat=3):
        mask = sum(bit * value for bit, value in zip(n.BITS[1:], bits, strict=True))
        text = b.render(fixture, mask)
        assert all((f"{actor} canary." in text) == bool(seen) for actor, seen in zip(b.ROLES, bits, strict=True))
        assert ("differed" in text) == bool(bits[0] and bits[1])
    return 8


def verify():
    with patch.object(n, "OUT", b.OUT), patch.object(r, "calls", calls):
        return r.verify() | {"visibility_fixture_masks": structure_check()}


def packets():
    _, source, _ = n.setup()
    case = {"id": source["id"], "task": source["task"], "rubric": source["rubric"], "track": "historical",
            "word_cap": n.LIMIT, "public": source["evidence"], "owned": []}
    pieces = fragments()
    rows = {}
    for mask in range(8):
        record = b.render(pieces, mask)
        calls = [{}, {}, {"text": record, "termination": "complete" if pieces["public"]["summary"] else "error"}]
        packet = e.final_packet(case, calls)
        received = ["vote", "operative", *(role.lower() for role, bit in zip(b.ROLES, n.BITS[1:]) if mask & bit)]
        rows[mask] = {"record": packet, "available": received, "calls": calls}
    return case, rows


def score():
    case, rows = packets()
    verdicts = n.read(b.HERE / "marks.json")
    assert set(verdicts) == {str(mask) for mask in rows}
    scores = {}
    for mask, row in rows.items():
        verdict = verdicts[str(mask)]
        assert all({x["block"] for x in grade["source"]} <= set(row["available"])
                   for grade in verdict["units"] if grade["status"] == "met")
        scores[mask] = e.final_score(case, row["calls"], verdict)
    return {"fragments": fragments(), "records": scores,
            "frozen_route_comparison": n.comparison({k: v["released_70"] for k, v in scores.items()}),
            "annotation": "same-assistant source reading"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("fragments", "verify", "packets", "score"))
    e.emit({"fragments": fragments, "verify": verify, "packets": lambda: packets()[1],
            "score": score}[parser.parse_args().mode]())
