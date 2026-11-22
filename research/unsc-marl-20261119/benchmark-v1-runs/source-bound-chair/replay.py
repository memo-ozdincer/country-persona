"""Replay real workshop declarations and audit the chair's public evidence contract."""
import argparse
from copy import deepcopy
from hashlib import sha256
from itertools import permutations
import json
from pathlib import Path
import sys

import chair

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
sys.path.insert(0, str(chair.ROOT / "benchmark"))
import evaluate as e
from run_suite import verify_release

IRAQ = RUNS / "iraq-certified-transfer/evidence/episodes.jsonl"
SYRIA = RUNS / "syria-targeted-clarification/results.json"
SYRIA_RAW = RUNS / "syria-targeted-clarification/evidence/responses.jsonl"


def disclosure(id_, role, requirement):
    return {"id": id_, "role": role, "requirement": requirement}


def declarations():
    for line in IRAQ.read_text().splitlines():
        row = json.loads(line)
        collected = [json.loads(row[k]["response"]["text"]) for k in ("first", "second")]
        typed = [{item["field"]: item["value"]} for item in collected]
        assert typed == row["extracted"]
        yield row["id"], [disclosure(f"{row['id']}/{i}", role, claim)
                          for i, (role, claim) in enumerate(zip(row["roles"], typed, strict=True))]
    raw = {row["id"]: row for row in map(json.loads, SYRIA_RAW.read_text().splitlines())}
    for key, row in e.read(SYRIA)["evaluation"]["records"].items():
        if not key.endswith("/raw"):
            continue
        name, _, order, _ = key.split("/")
        items = []
        for i, answer in enumerate(row["clarifications"]):
            receipt = raw[f"{key}/ask-{i}"]
            typed = json.loads(receipt["response"]["text"])
            claim = {typed["field"]: typed["value"]}
            assert claim == answer["declared"]
            items.append(disclosure(f"{key}/ask-{i}", answer["speaker"], claim))
        yield f"{name}/{order}", items


def mutate(packet, declarations, index):
    old = declarations[index]
    key, value = next(iter(old["requirement"].items()))
    alternatives = sorted({p[key] for p in packet["options"]} - {value})
    assert len(alternatives) == 1
    return disclosure(old["id"] + "/counterfactual", old["role"], {key: alternatives[0]})


def permuted(packet, labels):
    alternate = deepcopy(packet)
    for option in alternate["options"]:
        option["id"] = labels[option["id"]]
    alternate["options"].sort(key=lambda r: r["id"])
    public_menu = next(block for block in alternate["public"] if block["id"] == "menu")
    public_menu["text"] = "\n".join(f"{p['id']}: {p['text']}" for p in alternate["options"])
    return alternate


def driver():
    verify_release()
    cases = e.cases()
    result = {}
    counts = {"exact": 0, "one_missing_unresolved": 0, "both_missing_unresolved": 0,
              "conflicts_unresolved": 0, "unguarded_false_terminal": 0,
              "unguarded_false_wrong_terminal": 0, "guarded_false_unresolved": 0,
              "permutation_preserves_decision": 0}
    for key, turns in declarations():
        name, order = key.split("/")
        case = cases[name]
        packet = chair.project(case)
        role_local = dict(zip(case["roles"], case["membership"], strict=True))
        menu = packet["options"]
        assert [d["role"] for d in turns] == (case["roles"] if order == "0" else case["roles"][::-1])
        assert all(chair.filter_local(menu, d, role_local[d["role"]]) for d in turns)
        record = chair.render(packet, turns)
        assert record["decision"] in case["gold"]
        counts["exact"] += 1
        assert chair.render(packet, [])["decision"] == "UNRESOLVED"
        counts["both_missing_unresolved"] += 1
        failures = {}
        for i in (0, 1):
            kept = turns[1-i]
            assert chair.render(packet, [kept])["decision"] == "UNRESOLVED"
            counts["one_missing_unresolved"] += 1
            false = mutate(packet, turns, i)
            contradicts = chair.render(packet, turns + [false])
            assert contradicts["proof"]["state"] == "CONTRADICTORY_DISCLOSURE"
            assert contradicts["decision"] == "UNRESOLVED"
            counts["conflicts_unresolved"] += 1

            raw = chair.render(packet, [kept, false])
            filtered = [d for d in (kept, false) if chair.filter_local(menu, d, role_local[d["role"]])]
            assert filtered == [kept]
            verified = chair.render(packet, filtered)
            assert verified["decision"] == "UNRESOLVED"
            counts["guarded_false_unresolved"] += 1
            terminal = raw["decision"] != "UNRESOLVED"
            counts["unguarded_false_terminal"] += terminal
            counts["unguarded_false_wrong_terminal"] += terminal and raw["decision"] not in case["gold"]
            failures[turns[i]["role"]] = {"false_declaration": false, "unguarded": raw["decision"],
                                          "guarded": verified["decision"], "conflict": contradicts["proof"]}
        for order_variant in permutations("ABCD"):
            labels = dict(zip("ABCD", order_variant, strict=True))
            counter = chair.render(permuted(packet, labels), turns)
            assert counter["decision"] == labels.get(record["decision"], record["decision"])
            counts["permutation_preserves_decision"] += 1
        result[key] = {"declarations": turns, "record": record, "false_replacements": failures}
    assert set(result) == {f"{key}/{i}" for key in cases if cases[key]["track"] == "workshop" for i in range(2)}
    hashes = {str(path.relative_to(chair.ROOT)): sha256(path.read_bytes()).hexdigest()
              for path in (IRAQ, SYRIA, SYRIA_RAW, HERE / "chair.py", HERE / "protocol.md", Path(__file__),
                           chair.ROOT / "benchmark/release.json", chair.ROOT / "crossbench/decision_ledger.py")}
    return {"counts": counts, "records": result, "input_sha256": hashes}


def deck(data):
    output = {}
    cases = e.cases()
    for key, row in data["records"].items():
        case = cases[key.split("/")[0]]
        packet = e.final_packet(case, [{}, {}, {"text": row["record"]["text"]}])
        output[packet["id"]] = packet
    return [output[k] for k in sorted(output)]


def score(data, marks):
    cases = e.cases()
    assert set(marks) == {packet["id"] for packet in deck(data)}
    grades = {}
    for key, row in data["records"].items():
        case = cases[key.split("/")[0]]
        calls = [{}, {}, {"text": row["record"]["text"], "termination": "complete"}]
        packet = e.final_packet(case, calls)
        grades[key] = e.final_score(case, calls, marks[packet["id"]])
    tracks = {}
    for family in ("iraq", "syria"):
        chosen = [row for key, row in grades.items() if key.startswith(family)]
        tracks[family] = {"exact": sum(r["mechanical"]["accepted"] for r in chosen),
                          "strict": sum(r["strict"] for r in chosen),
                          "released": sum(r["release"] for r in chosen),
                          "released_70": sum(r["released_70"] for r in chosen)}
    return {"annotation": "same-assistant review of authored deterministic rendering",
            "families": tracks, "episodes": grades}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("replay", "deck", "score"))
    mode = cli.parse_args().mode
    current = driver()
    if mode == "deck":
        current = deck(current)
    elif mode == "score":
        current = score(current, e.read(HERE / "marks.json"))
    e.emit(current)
