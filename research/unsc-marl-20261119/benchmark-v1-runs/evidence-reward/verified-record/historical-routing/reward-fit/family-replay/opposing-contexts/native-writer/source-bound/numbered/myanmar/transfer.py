"""Transfer a locked, numbered-passage record pipeline to Myanmar."""
import argparse
from hashlib import sha256
from itertools import combinations, product
import json
from pathlib import Path
import sys
from unittest.mock import patch

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import numbered as old
import calibrate_pair as cal

n, m, e = old.n, old.n.matched, old.e
OUT = HERE / "evidence"
ARCHIVE = m.data.FILES["myanmar"]
ROLES = ("uk", "india", "chair")
CARDS = {
    "uk": {"4": "welcomed the result", "9": "The United Kingdom submitted the draft",
           "2": "consultations with Council members, ASEAN members and regional partners",
           "5": "It emphasized ending violence, humanitarian access and support for ASEAN efforts."},
    "india": {"3": "India praised the United Kingdom's consultation",
              "7": "noted neighbouring countries' concerns",
              "1": "advocated quiet, constructive diplomacy", "8": "explained its abstention in light of those concerns."},
    "chair": {"1": "then resumed the duties of President.",
              "6": "India held the Council presidency. The President called the vote and announced adoption.",
              "3": "India's representative later explained the national abstention"},
}
PURPOSE = {
    "uk": "Preserve the sponsor, relevant consultation, and priorities explaining support.",
    "india": "Preserve the regional concerns and quiet-diplomacy explanation for its national abstention.",
    "chair": "Preserve the Council president's procedural acts and the subsequent national explanation as separate functions.",
}
LABELS = {"uk": "United Kingdom", "india": "India as a delegation", "chair": "Council procedure"}
DEPENDENCIES = {"uk": {"uk"}, "india": {"india"}, "role": {"chair"}, "overlap": {"uk", "india"}}


def source_case():
    rows = n.read(ARCHIVE)["records"]
    row = next(r for r in rows if r["mask"] == 7)["packet"]
    return {"id": "myanmar-numbered-transfer", "task": row["task"], "rubric": row["rubric"],
            "track": "historical", "word_cap": n.LIMIT, "public": row["evidence"], "owned": []}


def calibration_pair(case):
    weights = {r["id"]: r["weight"] for r in case["rubric"]}
    pairs = tuple(combinations(ROLES, 2))
    value = {pair: sum(weights[key] for key, sources in DEPENDENCIES.items() if sources == set(pair))
             for pair in pairs}
    pair = max(pairs, key=value.__getitem__)
    return {"pair": list(pair) if value[pair] else [], "mask": sum(1 << ROLES.index(r) for r in pair) if value[pair] else 0,
            "pair_weights": {"/".join(key): score for key, score in value.items()}}


def plan():
    case = source_case()
    blocks = {r["id"]: r["text"] for r in case["public"]}
    recipes = {
        "vote": ["The Council adopted draft S/2022/980 as resolution 2669 (2022), by 12 votes in favour, none against and three abstentions.",
                 "The United Kingdom voted in favour. China, India and Russia abstained."],
        "mandate": ["demands an immediate end to violence, calls for humanitarian access, and acknowledges ASEAN's central role",
                    "the Secretary-General or his Special Envoy, in coordination with the ASEAN Special Envoy, to report orally to the Security Council by 15 March 2023"],
    }

    def span(role, phrase):
        start = blocks[role].index(phrase)
        return {"block": role, "text": phrase, "start": start, "end": start + len(phrase)}

    public = {role: [span(role, value) for value in values] for role, values in recipes.items()}
    cards = {role: {i: span(role, t) for i, t in menu.items()} for role, menu in CARDS.items()}
    requests = []
    for role, menu in cards.items():
        payload = {"task": case["task"], "delegation": LABELS[role], "passages": {k: x["text"] for k, x in menu.items()}}
        instruction = ("Select passage IDs needed for this source's contribution to the decision record. "
                       + PURPOSE[role] + " Return a JSON array of ID strings by importance. Prefer fewer IDs when an item is secondary. No prose.")
        requests.append({"part": role, "request": old.b.request(instruction, payload, 72)})
    files = (Path(__file__), HERE / "protocol.md", ARCHIVE, n.WITNESS, Path(cal.__file__), Path(old.__file__))
    return {"requests": requests, "public": public, "cards": cards, "calibration": calibration_pair(case),
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in files}}


def collect(generate, folder):
    current = plan()
    assert current == n.read(HERE / "plan.json")
    for request in current["requests"]:
        n.base.suite.append(folder / "calls.jsonl", request | {"response": generate(request["request"])})


def calls():
    rows = n.lines(OUT / "calls.jsonl")
    assert [{k: row[k] for k in ("request", "part")} for row in rows] == plan()["requests"]
    return rows


def choose_ids(row):
    with patch.object(old, "MENUS", CARDS):
        return old.selection(row["part"], row["response"])


def enough(role, ids):
    if role == "india":
        return bool({"7", "1"} & ids)
    return {"uk": {"9", "5"}, "chair": {"6", "3"}}[role] <= ids


def overlaps(slots):
    return "2" in slots["uk"] and "7" in slots["india"]


def pack(mask, selected, deck):
    v1, v2 = [x["text"] for x in deck["public"]["vote"]]
    mn, re = [x["text"] for x in deck["public"]["mandate"]]
    public = f"{v1} {v2} The resolution {mn}. It requests {re}."
    pieces = [(role, item, len(ids) - p) for bit, (role, ids) in zip(n.BITS[1:], selected.items())
              if bit & mask for p, item in enumerate(ids)]
    best = None
    for used in product((False, True), repeat=len(pieces)):
        slots = {role: set() for role in ROLES}
        weight = 0
        for keep, (role, item, priority) in zip(used, pieces):
            if keep:
                slots[role].add(item)
                weight += priority
        if ("8" in slots["india"] and "7" not in slots["india"]) or ("3" in slots["chair"] and "6" not in slots["chair"]):
            continue
        paragraphs = [public]
        for role in ROLES:
            if slots[role]:
                spans = sorted([deck["cards"][role][i] for i in slots[role]], key=lambda row: row["start"])
                paragraphs.append(LABELS[role] + " — " + " ".join("“" + r["text"] + "”" for r in spans))
        if overlaps(slots):
            paragraphs.append("Both delegations addressed regional concerns, while their votes differed.")
        text = "\n\n".join(paragraphs)
        count = len(text.split())
        if count > n.LIMIT:
            continue
        merit = (sum(bool(v) for v in slots.values()), weight, count)
        if best is None or merit > best[0]:
            best = merit, {"text": text, "words": count, "used": {k: sorted(v) for k, v in slots.items()}}
    assert best is not None
    return best[1]


def verify():
    assert n.read(HERE / "plan.json") == plan()
    with patch.object(n, "OUT", OUT), patch.object(old.audit, "calls", calls):
        receipt = old.audit.verify()
    outputs = {role: list(menu) for role, menu in CARDS.items()}
    for mask in range(8):
        row = pack(mask, outputs, plan())
        assert all(not (mask & bit == 0 and row["used"][r]) for r, bit in zip(ROLES, n.BITS[1:]))
    return receipt | {"visibility_masks": 8, "calibration": calibration_pair(source_case())}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    if mode == "run":
        with patch.object(n.base.suite, "collect", collect), patch.object(
                n.base, "roster", return_value={"myanmar-numbered-transfer": None}):
            n.base.run(OUT)
    else:
        e.emit(plan() if mode == "plan" else verify())
