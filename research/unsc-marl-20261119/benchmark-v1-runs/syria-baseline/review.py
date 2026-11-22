"""Project blind final packets and compute source-checked note and final diagnostics."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

from collect import HERE, roster, suite

sys.path.insert(0, str(HERE.parents[1] / "crossbench"))
import decision_ledger as ledger

EVIDENCE = HERE / "evidence"
E = suite.e


def episodes():
    for line in (EVIDENCE / "episodes.jsonl").read_text().splitlines():
        row = json.loads(line)
        case, arm, order = row["id"].split("/")
        order = int(order)
        case = roster()[case]
        yield row["id"], case, arm, order, E.validate_calls(case, arm, order, row["calls"])


def packets(kind):
    output = {}
    for key, case, arm, order, calls in episodes():
        if kind == "finals":
            f = E.final_packet(case, calls)
            output[f["id"]] = f
        else:
            key = "notes-" + E.checksum([case["id"], [r["text"] for r in calls[:2]]])[:16]
            output[key] = {"id": key, "notes": [x["text"] for x in calls[:2]],
                           "speakers": [x["speaker"] for x in calls[:2]], "menu": case["options"],
                           "roles": case["roles"]}
    return [out for _, out in sorted(output.items())]


def public_readout(case, calls, marks):
    roles = case["roles"]
    options = case["options"]
    order = [p["id"] for p in options]
    facts = []
    truthful = []
    requirements = {role: {} for role in roles}
    seen = set()
    for row in marks:
        turn, role, field, value = [row[k] for k in ("turn", "role", "field", "value")]
        assert turn in (0, 1) and role in roles and row["span"].strip() and row["span"] in calls[turn]["text"]
        allowed = {p["id"] for p in options if p[field] == value}
        assert allowed and (turn, role, field, value) not in seen
        seen.add((turn, role, field, value))
        if field == "id":
            assert row["force"] == "endorsement"
            message = {"id": str(len(facts)), "role": role, "accepts": [value], "excludes": []}
        else:
            message = {"id": str(len(facts)), "role": role, "accepts": [], "excludes": [p for p in order if p not in allowed]}
            if row["force"] == "complete":
                message["accepts"] = [p for p in order if p in allowed]
            else:
                assert row["force"] == "requirement_only"
            requirements[role].setdefault(field, set()).add(value)
        facts.append(message)
        private = case["membership"][roles.index(role)]
        compatible = [p["id"] for p in options if all(p[k] == v for k, v in private.items())]
        truthful.append(ledger.truthful_disclosure(message, compatible))
    readout = ledger.readout(order, roles, facts)
    state = readout["state"]
    supported = (list(readout["verified_options"]) if state == "AGREEMENT_POSSIBLE"
                 else ["IMPASSE"] if state == "IMPASSE" else [])
    inferred = None
    if all(r and all(len(values) == 1 for values in r.values()) for r in requirements.values()):
        inferred = [p["id"] for p in options if all(
            p[field] in values for r in requirements.values() for field, values in r.items())]
        inferred = inferred or ["IMPASSE"]
    return {"ledger": readout, "disclosure_truth": truthful,
            "certifies_key": all(truthful) and bool(set(supported) & set(case["gold"])),
            "requirements_only_inference": inferred,
            "requirements_recover_key": inferred is not None and bool(set(inferred) & set(case["gold"])),
            "false_endorsements": sum(row["field"] == "id" and not ok
                                      for row, ok in zip(marks, truthful, strict=True)),
            "speaker_own_requirement_present": {
                str(i): any(item["turn"] == i and item["field"] != "id" and item["role"] == calls[i]["speaker"] and ok
                            for item, ok in zip(marks, truthful, strict=True))
                for i in (0, 1)
            }}


def score(note_marks, final_marks):
    out = {}
    for key, case, arm, order, calls in episodes():
        np = "notes-" + E.checksum([case["id"], [r["text"] for r in calls[:2]]])[:16]
        fp = E.final_packet(case, calls)
        verdict = final_marks[fp["id"]]
        result = E.final_score(case, calls, verdict)
        notes = public_readout(case, calls, note_marks[np])
        out[key] = {**result, "notes": notes, "notes_review_id": np, "final_review_id": fp["id"],
                    "input_tokens": sum(r["input_tokens"] for r in calls)}
    aggregate = {}
    for arm in E.ARMS:
        group = [r for key, r in out.items() if key.split("/")[1] == arm]
        aggregate[arm] = {"certified_from_notes": sum(r["notes"]["certifies_key"] for r in group),
                          "exact_decisions": sum(r["mechanical"]["accepted"] for r in group),
                          "raw_lower_sum": sum(r["raw_70"][0] for r in group),
                          "released_sum": sum(r["released_70"] for r in group),
                          "release": sum(r["release"] for r in group),
                          "decision_counts": dict(Counter(r["mechanical"]["decision"] or "invalid" for r in group))}
    return {"arms": aggregate, "episodes": out}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("notes", "finals", "score"))
    args = cli.parse_args()
    if args.mode == "score":
        E.emit(score(E.read(HERE / "notes-marks.json"), E.read(HERE / "final-marks.json")))
    else:
        E.emit(packets(args.mode))
