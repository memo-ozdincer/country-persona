"""Generate two dated handover lines without a menu of possible dates."""
import argparse
from datetime import date, datetime
import json
from pathlib import Path
import re
import sys
from unittest.mock import patch

import receipt_handovers as prior

HERE = prior.HERE
sys.path.insert(0, str(HERE.parent / "validity-audit"))
import source_record_run as runner

FAMILY = "open-date-handover"
CAP = 84


def requests():
    for case in prior.fixtures()["inputs"]:
        fields = list(case["draft"])
        records = {i: body for i, body in case["holdings"].items() if body is not None}
        for arm in prior.ARMS:
            contents = {
                "task": ("Write the calendar handover. Use only a source that establishes this exact field. "
                         "For a confirmed or corrected date output its ISO date and documentary card ID. "
                         "If the cards do not establish the field, use verify and put a dash in both later columns. "
                         "Output exactly two lines in the format F1|action|date|source and F2|action|date|source. "
                         "Use only the actions confirm, correct and verify. No heading or explanation."),
                "draft_fields": {f"F{i+1}": {"field": field, "draft_date": case["draft"][field]} for i, field in enumerate(fields)},
                "documentary_cards": records,
            }
            if arm == "field_receipt":
                contents["explicit_field_receipts"] = {
                    f"F{i+1}": {"source_for_this_field": sid, "received": sid in records}
                    for i, (_, _, sid) in enumerate(prior.handover.CASES[case["family"]])
                }
            yield {"id": f"{case['id']:02}/{arm}", "cap": CAP,
                   "messages": [{"role": "system", "content": "You are the archival scheduling clerk preparing the next Council handover."},
                                {"role": "user", "content": json.dumps(contents, ensure_ascii=False)}]}


def episode(generate):
    rows = list(requests())
    results = {}
    # Bounded microbatches keep the run usable on the shared CPU.
    for i in range(0, len(rows), 16):
        results.update(generate(rows[i:i + 16]))
    return [{"family": FAMILY, "final": results}]


def locks():
    from hashlib import sha256
    files = (Path(__file__), Path(runner.__file__), *(HERE.parents[1] / p for p in prior.hashes()))
    return {str(p.relative_to(HERE.parents[1])): sha256(p.read_bytes()).hexdigest() for p in files}


def replay(directory):
    from transformers import AutoTokenizer

    launch, end = (prior.load(directory / name) for name in ("launch.json", "complete.json"))
    trace = directory / "transcript.jsonl"
    final = directory / "final-records.json"
    assert launch["sha256"] == locks() and end["transcript_sha256"] == runner.digest(trace)
    assert end["final_records_sha256"] == runner.digest(final)
    rows = {r["id"]: r for r in map(json.loads, trace.read_text().splitlines())}
    wanted = {r["id"]: r for r in requests()}
    assert rows.keys() == wanted.keys() and len(rows) == end["records"] == 64
    tokenizer = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    token = tokenizer.convert_tokens_to_ids("<|im_end|>")
    for key, request in wanted.items():
        row = rows[key]
        assert all(row[k] == value for k, value in request.items())
        assert runner.encode(tokenizer, request) == row["input_ids"]
        ids = row["output_ids"]
        assert 0 < len(ids) <= CAP and token not in ids[:-1] and row["ended"] == (ids[-1] == token)
        assert row["output"] == tokenizer.decode(ids, skip_special_tokens=True).strip()
    assert prior.load(final) == {FAMILY: {key: row["output"] for key, row in rows.items()}}
    return rows


def as_iso(spoken):
    return datetime.strptime(spoken, "%d %B %Y").date().isoformat() if spoken else None


def decode(text):
    lines = text.strip().splitlines()
    if len(lines) == 4 and lines[0] in ("\x60\x60\x60", "\x60\x60\x60text") and lines[-1] == "\x60\x60\x60":
        lines = lines[1:-1]
    predictions = {}
    for line in lines:
        match = re.fullmatch(r"F([12])\s*\|\s*(confirm|correct|verify)\s*\|\s*([0-9-]+)\s*\|\s*([A-Z]+|-)", line.strip())
        if not match:
            return None
        slot, action, proposed, sid = match.groups()
        if slot in predictions:
            return None
        if action == "verify":
            if (proposed, sid) != ("-", "-"):
                return None
        else:
            try:
                if proposed != date.fromisoformat(proposed).isoformat() or sid == "-":
                    return None
            except ValueError:
                return None
        predictions[slot] = (action, proposed, sid)
    return predictions if predictions.keys() == {"1", "2"} else None


def score(directory):
    rows = replay(directory)
    dataset = prior.fixtures()
    measures = {}
    for arm in (*prior.ARMS, "field_receipt_with_gate"):
        field_accuracy = []
        full = 0
        formats = 0
        outcomes = []
        unsupported = 0
        for case, key in zip(dataset["inputs"], dataset["keys"], strict=True):
            row = rows[f"{case['id']:02}/{'field_receipt' if arm.endswith('with_gate') else arm}"]
            parsed = decode(row["output"]) if row["ended"] else None
            formats += parsed is not None
            limited = parsed or {}
            handover = []
            for position, (field, _, sid) in enumerate(prior.handover.CASES[case["family"]], start=1):
                pred = limited.get(str(position), ("invalid", "-", "-"))
                required = (key["actions"][field], as_iso(key["deliverable"][field]) or "-",
                            "-" if key["actions"][field] == "verify" else sid)
                if arm.endswith("with_gate") and case["holdings"][sid] is None:
                    pred = ("verify", "-", "-")
                correct = pred == required
                field_accuracy.append((required[0], correct))
                unsupported += pred[0] in ("correct", "confirm") and required[0] == "verify"
                handover.append({"field": field, "expected": required, "observed": pred, "exact": correct})
            full += all(v["exact"] for v in handover)
            outcomes.append({"case": case["id"], "family": case["family"], "generation": row["output"],
                             "format_ok": parsed is not None, "output_tokens": len(row["output_ids"]),
                             "fields": handover})
        by_action = {name: {"correct": sum(ok for kind, ok in field_accuracy if name == kind),
                            "total": sum(name == kind for kind, _ in field_accuracy)}
                     for name in ("confirm", "correct", "verify")}
        routing = {}
        for inventory in ("overlap", "split"):
            routing[inventory] = {}
            for peer in (True, False):
                masks = prior.exact_receipt_probabilities(inventory, peer)
                usable = sum(masks[r["case"] % 4] / 8 for r in outcomes if r["case"] % 4 == 3
                             and all(v["exact"] for v in r["fields"]))
                field_exact = sum(masks[r["case"] % 4] / 8 * sum(v["exact"] for v in r["fields"])
                                  for r in outcomes)
                routing[inventory]["visible" if peer else "erased"] = {"complete_usable": usable, "correct_fields_of_two": field_exact}
        measures[arm] = {"exact_fields": sum(ok for _, ok in field_accuracy),
                         "exact_handovers": full, "valid_generated_format": formats,
                         "unsupported_certifications": unsupported, "by_action": by_action,
                         "routing": routing, "cases": outcomes}
    return {"scope": "Frozen generation of unrestricted ISO date strings and source IDs. "
                     "The source mapping is supplied to the receipt arm and absence gate. "
                     "The output syntax and action menu are fixed. Archived policies and synthetic receipt masks drive the exact replay.",
            "arms": measures}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "score"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, episode=episode, locks=locks):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps(score(args.directory), indent=2))
