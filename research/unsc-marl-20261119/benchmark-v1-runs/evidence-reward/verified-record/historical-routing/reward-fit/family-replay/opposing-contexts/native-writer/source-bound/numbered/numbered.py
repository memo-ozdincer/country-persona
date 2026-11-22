"""Select source-indexed passages and render records without free-form attribution."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import bound_writer as b
import read_native as audit

n, e = b.n, b.e
OUT = HERE / "evidence"
PUBLIC = (
    ("vote", "31 August 2023"),
    ("vote", "draft S/2023/641 submitted by France"),
    ("vote", "adopted as resolution 2695 (2023) by 13 votes in favour and none against, with China and the Russian Federation abstaining"),
    ("operative", "extended UNIFIL's existing mandate until 31 August 2024"),
    ("operative", "independence in carrying out mandated tasks without prior permission"),
    ("operative", "continued coordination with Lebanon's Government under the status-of-forces agreement"),
)
MENUS = {
    "brazil": {
        "8": "while addressing some of Lebanon's concerns",
        "3": "Brazil supported UNIFIL's continuing work",
        "6": "It judged that the French text kept the mandate robust and allowed UNIFIL to operate freely",
    },
    "china": {
        "1": "supported closer communication between UNIFIL and Lebanon's Government and military",
        "7": "China supported UNIFIL's work but said the text did not fully address Lebanon's concerns",
        "5": "It stressed host-State sovereignty and consent",
    },
    "russia": {
        "4": "called for coordination with Lebanon's Government",
        "9": "Russia attributed its abstention to contentious late drafting changes and said the final text lost a prior compromise",
        "2": "It continued to support the mission's activities",
    },
}
COMPARE = {"brazil": {"3", "8"}, "china": {"7"}}
PURPOSE = {
    "brazil": "Keep mission support, what the text did for operational freedom, and the qualified concern about Lebanon.",
    "china": "Keep mission support, whether the text did enough for Lebanon's concerns, and sovereignty or consent.",
    "russia": "Keep the reason for abstention, what happened to the prior compromise, and Russia's mission position.",
}


def plan():
    _, case, _ = n.setup()
    evidence = {r["id"]: r["text"] for r in case["evidence"]}

    def span(block, text):
        start = evidence[block].index(text)
        return {"block": block, "start": start, "end": start + len(text), "text": text}

    public = [span(k, value) for k, value in PUBLIC]
    cards = {role: {i: span(role, value) for i, value in entries.items()} for role, entries in MENUS.items()}
    rows = []
    for role, entries in cards.items():
        payload = {"task": case["task"], "delegation": role,
                   "passages": {i: item["text"] for i, item in entries.items()}}
        system = ("Select only the passage IDs necessary to preserve this delegation's position. "
                  + PURPOSE[role] +
                  " Prefer fewer IDs when a passage adds only a secondary detail. "
                  "Return a JSON array of ID strings in order of importance. Return no prose.")
        rows.append({"part": role, "request": b.request(system, payload, 72)})
    pins = (Path(__file__), HERE / "protocol.md", n.CASE_PATH, n.WITNESS)
    return {"requests": rows, "public": public, "cards": cards,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in pins}}


def collect(generate, directory):
    current = plan()
    assert n.read(HERE / "plan.json") == current
    for row in current["requests"]:
        n.base.suite.append(directory / "calls.jsonl", row | {"response": generate(row["request"])})


def calls():
    current = plan()
    assert n.read(HERE / "plan.json") == current
    rows = n.lines(OUT / "calls.jsonl")
    assert [{k: row[k] for k in ("part", "request")} for row in rows] == current["requests"]
    return rows


def selection(role, reply):
    if reply["termination"] != "complete":
        return [], "noncompletion"
    try:
        ids = json.loads(reply["text"])
    except json.JSONDecodeError:
        return [], "invalid_json"
    if (not isinstance(ids, list) or not ids or not all(isinstance(i, str) and i in MENUS[role] for i in ids)
            or len(set(ids)) != len(ids)):
        return [], "invalid_role_selection"
    return ids, "admitted"


def render(mask, chosen):
    deck = plan()
    day, draft, outcome, mandate, independence, coordination = [u["text"] for u in deck["public"]]
    public = f"{day}. The Council considered {draft}, {outcome}. It {mandate}, reaffirming {independence} and {coordination}."
    slots = {role: [] for role in deck["cards"]}
    ranks = {role: chosen[role] for bit, role in zip(n.BITS[1:], slots) if mask & bit}

    def write():
        paragraphs = [public]
        for role, available in slots.items():
            if not available:
                continue
            units = sorted([deck["cards"][role][i] for i in available], key=lambda row: row["start"])
            # Preserve exact wording even for disconnected excerpts.
            paragraphs.append(role.title() + " — " + " ".join("“" + r["text"] + "”" for r in units))
        if all(ids <= set(slots[role]) for role, ids in COMPARE.items()):
            paragraphs.append("Brazil and China backed UNIFIL but differed on how far the text addressed Lebanese concerns.")
        return "\n\n".join(paragraphs)

    for level in range(max(map(len, ranks.values()), default=0)):
        for role, ids in ranks.items():
            if level < len(ids):
                slots[role].append(ids[level])
                if len(write().split()) > n.LIMIT:
                    slots[role].pop()
    return {"text": write(), "used": slots}


def verify():
    with patch.object(n, "OUT", OUT), patch.object(audit, "calls", calls):
        receipt = audit.verify()
    for bad in ('[]', '["7"]', '["3","3"]', '[3]', '{"pick":"3"}'):
        assert selection("brazil", {"termination": "complete", "text": bad})[0] == []
    full = {role: list(items) for role, items in MENUS.items()}
    for mask in range(8):
        row = render(mask, full)
        assert len(row["text"].split()) <= n.LIMIT
        for bit, role in zip(n.BITS[1:], MENUS):
            assert bool(row["used"][role]) == bool(mask & bit)
    return receipt | {"visibility_masks": 8, "bad_selection_checks": 5}


def records():
    reviews = {row["part"]: selection(row["part"], row["response"]) for row in calls()}
    native = {role: row[0] for role, row in reviews.items()}
    all_passages = {role: list(items) for role, items in MENUS.items()}
    first = {role: ids[:1] for role, ids in all_passages.items()}
    return {"selection": reviews, "records": {
        key: {i: render(i, choice) for i in range(8)}
        for key, choice in (("native", native), ("all_passages", all_passages), ("first_menu_item", first))}}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("plan", "run", "verify", "records"))
    mode = cli.parse_args().mode
    if mode == "run":
        with patch.object(n.base.suite,"collect",collect), patch.object(
                n.base, "roster", return_value={"matched-unifil-numbered-writer": None}):
            n.base.run(OUT)
    else:
        e.emit({"plan": plan, "verify": verify, "records": records}[mode]())
