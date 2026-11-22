"""Build source-attributed records from selected role-local evidence IDs."""
import argparse
from itertools import combinations, product
import json
from pathlib import Path
from statistics import mean
from unittest.mock import patch

from select_notes import BRIDGE, CASE, HERE, MENUS, PARENT, PUBLIC, READ, REQUIRED, frozen, prior

PUBLIC_KEYS = ("decision", "action", "report")
GOLD = [["1"], ["1", "2"], ["1", "2"]]
KEY_SOURCES = {key: (key,) for key in REQUIRED} | {
    "fr-ru-scope": ("fr-treaty", "ru-article"), "uk-ru-ground": ("uk-authority",)}
KEY_SOURCES.update({key: (key,) for key in PUBLIC_KEYS})


def render(selection, mask):
    selected = set()
    for desk, ids in enumerate(selection):
        assert len(ids) == len(MENUS[desk]) - 1 and len(set(ids)) == len(ids) and set(ids) <= MENUS[desk].keys()
        if mask & 1 << desk:
            selected.update((desk, code) for code in ids)
    parts = [PUBLIC] + [text for desk, menu in enumerate(MENUS)
                        for code, (_, text) in menu.items() if (desk, code) in selected]
    scope = all(REQUIRED[claim] in selected for claim in ("fr-treaty", "ru-article"))
    if scope:
        parts.append(BRIDGE)
    answer = "\n\n".join(parts)
    claims = {key: PUBLIC for key in PUBLIC_KEYS}
    claims.update({key: MENUS[i][code][1] for key, (i, code) in REQUIRED.items() if (i, code) in selected})
    if scope:
        claims["fr-ru-scope"] = BRIDGE
    if "uk-authority" in claims:
        claims["uk-ru-ground"] = claims["uk-authority"]
    sources = {row["id"]: row["text"] for row in frozen.evidence(CASE)}
    calls = [{}, {}, {"text": answer, "termination": "complete"}]
    packet = frozen.final_packet(CASE, calls)
    units = [{"id": rule["id"], "status": "met" if rule["id"] in claims else "unmet",
              "response": claims.get(rule["id"], ""),
              "source": [{"block": k, "quote": sources[k]} for k in KEY_SOURCES[rule["id"]]]
                        if rule["id"] in claims else [],
              "reason": "This exact source-scoped clause is present." if rule["id"] in claims
                        else "A required proof passage is absent."} for rule in CASE["rubric"]]
    marks = {"id": packet["id"], "units": units,
             "guard": {"status": "clear", "source": [], "response": "",
                       "reason": "Every rendered clause is held under its preverified source ownership."}}
    score = frozen.final_score(CASE, calls, marks)
    assert score["release"]
    return {"text": answer, "marks": marks, "score": score,
            "selected_ids": sorted(selected), "contrast_rendered": scope}


def score():
    verified = READ(HERE / "verified.json")
    selections = verified["selections"]
    outputs = {"authored": GOLD} | {f"{order}/{label}": [selections[f"{order}/{i}"][label] for i in range(3)]
                                     for order, label in product(("normal", "reversed"), ("native", "canonical", "first"))}
    records = {name: [render(groups, mask) for mask in range(8)] for name, groups in outputs.items()}
    banks = {name: [row["score"]["released_70"] for row in values] for name, values in records.items()}
    assert banks["authored"] == READ(PARENT / "oracle.json")["authored_bank"]
    assert banks["normal/first"] == banks["authored"]
    assert outputs["reversed/first"] != GOLD
    options = [list(combinations(menu, len(menu) - 1)) for menu in MENUS]
    scores = [render(select, 7)["score"]["released_70"] for select in product(*options)]
    assert len(scores) == 18 and scores.count(70) == 1
    return {"banks": banks, "records": records, "selections": outputs,
            "uniform_control": {"legal_combinations": len(scores), "mean_full_receipt": mean(scores),
                                "strict_full_receipt": scores.count(70) / len(scores)},
            "sha256": {p.name: prior.digest(p) for p in (Path(__file__), HERE / "verified.json", HERE / "plan.json")}}


def route():
    import route_2475 as locked

    local = HERE / "scores.json"
    banks = READ(local)["banks"]
    by_bank = {}
    for name, points in banks.items():
        by_bank.setdefault(tuple(points), []).append(name)
    distinct = {modes[0]: list(values) for values, modes in by_bank.items()}
    read = locked.READ

    def choose(path):
        if Path(path) == PARENT / "scores.json":
            return {"banks": distinct}
        return read(path)

    with patch.object(locked, "READ", choose):
        result = locked.run()
    assert result["policy_replays"] == len(distinct) * 72
    result["sha256"]["scores.json"] = prior.digest(local)
    result["sha256"]["compose_notes.py"] = prior.digest(Path(__file__))
    result["condition_aliases"] = {name: aliases[0] for aliases in by_bank.values() for name in aliases}
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("score", "route"))
    frozen.emit({"score": score, "route": route}[parser.parse_args().mode]())
