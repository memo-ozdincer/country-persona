"""Enforce claim availability before emitting the one permitted relation."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import patch

from choose_relation import CASE, HERE, LABELS, PARENT, READ, RELATIONS, conditions, frozen, prior

MASKS = {3: "pair", 7: "full"}
RESTORED = READ(PARENT / "oracle.json")["authored_records"]["7"]["answer"].split("\n\n")
REQUIRED = {"fr-treaty": ("France", RESTORED[1]),
            "ru-article": ("Russian Federation", RESTORED[2])}


def admitted_ids(notes):
    return {claim for claim, (owner, excerpt) in REQUIRED.items()
            if any(row["owner"] == owner and excerpt == row["text"] for row in notes)}


def support(verified):
    tests = READ(HERE / "plan.json")["targets"]
    outputs = verified["outputs"]
    rows = {}
    for name, truth in tests.items():
        orders = {}
        for mapping in LABELS:
            stored = outputs[f"{name}/{mapping}"]
            labels = LABELS[mapping]
            yes, no = [letter for letter, answer in labels.items() if answer], [
                letter for letter, answer in labels.items() if not answer]
            margin = stored["logits"][yes[0]] - stored["logits"][no[0]]
            orders[mapping] = {"prediction": labels[stored["label"]], "support_minus_unsupported": margin}
        ab, ba = (row["prediction"] for row in orders.values())
        margins = [row["support_minus_unsupported"] for row in orders.values()]
        rows[name] = {"truth": truth, "orders": orders, "consensus": ab if ab == ba else None,
                      "mean_logit": sum(margins) > 0 if sum(margins) else None}
    summary = {}
    for mode in ("ab", "ba", "consensus", "mean_logit"):
        predictions = [(row["truth"], row[mode] if mode in row else row["orders"][mode]["prediction"])
                       for row in rows.values()]
        summary[mode] = {"exact": sum(prediction is truth for truth, prediction in predictions),
                         "supports_true": sum(prediction is True and truth for truth, prediction in predictions),
                         "supports_false": sum(prediction is True and not truth for truth, prediction in predictions),
                         "abstains": sum(prediction is None for _, prediction in predictions)}
    assert len(rows) == 10 and sum(tests.values()) == 4
    return rows, summary


def render(record, notes, consensus):
    available = admitted_ids(notes)
    present = available == set(REQUIRED)
    if present and consensus:
        return record + "\n\n" + RELATIONS["scope"], available
    return record, available


def run():
    verified = READ(HERE / "verified.json")
    rows, summary = support(verified)
    baseline = READ(PARENT / "scope-bridge/scores.json")["scores"]
    inputs = READ(PARENT / "scope-bridge/verified.json")["records"]
    evidence = {row["id"]: row["text"] for row in frozen.evidence(CASE)}
    request_plan = READ(HERE / "plan.json")["requests"]
    banks, records = {}, {}
    for source in ("native", "authored"):
        for mode in ("none", "rule", "gated"):
            series = []
            for mask in range(8):
                key = f"{source}/none/mask-{mask}"
                record = inputs[key]
                text = record["text"]
                ids = set()
                if mode != "none" and mask in MASKS:
                    item = f"{source}_{MASKS[mask]}"
                    notes = json.loads(request_plan[f"{item}/ab"]["messages"][1]["content"])["notes"]
                    decision = mode == "rule" or rows[item]["consensus"] is True
                    text, ids = render(text, notes, decision)
                calls = [{}, {}, {**record, "text": text}]
                packet = frozen.final_packet(CASE, calls)
                marks = deepcopy(baseline[key]["marks"])
                marks["id"] = packet["id"]
                if text != record["text"]:
                    assert ids == set(REQUIRED) and text.endswith(RELATIONS["scope"])
                    for unit in marks["units"]:
                        if unit["id"] == "fr-ru-scope":
                            unit.update(status="met", response=RELATIONS["scope"],
                                        source=[{"block": block, "quote": evidence[block]} for block in REQUIRED],
                                        reason="The approved template keeps the two sourced positions and their instruments distinct.")
                grade = frozen.final_score(CASE, calls, marks)
                summary_id = f"{source}/{mode}/mask-{mask}"
                records[summary_id] = {"answer": text, "marks": marks, "score": grade,
                                       "admitted_claim_ids": sorted(ids), "relation_added": text != record["text"]}
                series.append(grade["released_70"])
            banks[f"{source}/{mode}"] = series

    assert banks["native/none"] == banks["native/rule"] == banks["native/gated"]
    assert banks["authored/rule"] == READ(PARENT / "oracle.json")["authored_bank"]
    cases = conditions()
    for name, role in (("omit_france_treaty", "fr-treaty"), ("omit_russia_reading", "ru-article")):
        _, texts, _ = cases[name]
        notes = [{"owner": owner, "text": text} for owner, text in zip(CASE["roles"][:len(texts)], texts, strict=True)]
        result, markers = render("Existing record", notes, True)
        assert result == "Existing record" and role not in markers
    wrong_owner = [{"owner": "United Kingdom", "text": RESTORED[1]},
                   {"owner": "Russian Federation", "text": RESTORED[2]}]
    negation = [{"owner": "France", "text": "The following assertion is incorrect: " + RESTORED[1]},
                {"owner": "Russian Federation", "text": RESTORED[2]}]
    assert all(render("Existing record", notes, True)[0] == "Existing record"
               for notes in (wrong_owner, negation))
    return {"classification": {"rows": rows, "summary": summary}, "banks": banks, "records": records,
            "sha256": {p.name: prior.digest(p) for p in (Path(__file__), HERE / "verified.json",
                        HERE / "plan.json", PARENT / "scope-bridge/scores.json")}}


def route():
    import route_2475 as locked

    score_path = HERE / "scored.json"
    banks = READ(score_path)["banks"]
    # The native bank is shared by all three methods. Retain one copy in the replay.
    distinct = {name: points for name, points in banks.items()
                if name in {"native/gated", "authored/none", "authored/rule", "authored/gated"}}
    read = locked.READ

    def access(path):
        if Path(path) == PARENT / "scores.json":
            return {"banks": distinct}
        return read(path)

    with patch.object(locked, "READ", access):
        result = locked.run()
    assert result["policy_replays"] == 288
    assert result["results"]["native/gated"] == READ(PARENT / "routing.json")["results"]["verbatim"]
    result["sha256"].pop("scores.json")
    result["sha256"]["scored.json"] = prior.digest(score_path)
    result["sha256"]["render_bound.py"] = prior.digest(Path(__file__))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("score", "route"))
    frozen.emit({"score": run, "route": route}[parser.parse_args().mode]())
