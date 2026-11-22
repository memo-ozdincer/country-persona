"""Read one unrestricted date from its bound source without asking the model for an action label."""
import argparse
from datetime import date
import json
from pathlib import Path
from unittest.mock import patch

import open_handover as prior

HERE = prior.HERE
runner = prior.runner
COLOMBIA = prior.prior.handover.CROSS / "colombia2023/case.json"
FAMILY = "isolated-date"
CAP = 30


def controls():
    operative = prior.prior.load(COLOMBIA)["public"]["OPERATIVE"]
    expiry = "expiry date of the existing UN Verification Mission mandate in Colombia"
    future = "date on which the Council authorized a further extension of that mandate"
    for field, gold in ((expiry, "2024-10-31"), (future, None)):
        for claimed in ("31 October 2024", "1 November 2024"):
            for card in (operative, None):
                yield "colombia", field, claimed, card, gold if card else None
    source = prior.prior.load(prior.prior.handover.CROSS / "drc2023/case.json")["sources"]["EXPERTS"]["card"]
    swapped = source.replace("1 August 2024", "{expiry}").replace("1 July 2024", "1 August 2024").replace("{expiry}", "1 July 2024")
    for text, term, review in ((source, "2024-08-01", "2024-07-01"), (swapped, "2024-07-01", "2024-08-01")):
        for field, gold in (("expiry of the Group of Experts mandate", term),
                            ("date by which the Council intended to review and act on a possible further extension", review)):
            yield "drc_control", field, "1 July 2024", text, gold


def request(key, field, draft, card):
    task = ("Return just the ISO date YYYY-MM-DD that the documentary card establishes for this exact field. "
            "The draft is provisional. Dates for other acts or other time limits do not establish the requested date. "
            "Pay attention to whether the Council actually enacted the item or only intended to consider it. "
            "If the card does not establish this field, return UNKNOWN. Do not write anything else.")
    return {"id": key, "cap": CAP, "messages": [
        {"role": "system", "content": task},
        {"role": "user", "content": json.dumps({"field": field, "provisional_draft_date": draft,
                                               "bound_documentary_card": card}, ensure_ascii=False)},
    ]}


def cases():
    source = prior.prior.fixtures()
    for entry, key in zip(source["inputs"], source["keys"], strict=True):
        for pos, (field, _, sid) in enumerate(prior.prior.handover.CASES[entry["family"]]):
            card = entry["holdings"][sid]
            yield (f"{entry['id']:02}/{pos}", entry["family"], field, entry["draft"][field], card,
                   prior.as_iso(key["deliverable"][field]), entry["id"], sid)
    for n, (family, field, draft, card, gold) in enumerate(controls()):
        yield f"control/{n:02}", family, field, draft, card, gold, None, None


def requests():
    return [request(key, field, draft, card) for key, _, field, draft, card, _, _, _ in cases()]


def episode(generate):
    wanted = requests()
    outputs = {}
    for start in range(0, len(wanted), 16):
        outputs.update(generate(wanted[start:start+16]))
    return [{"family": FAMILY, "final": outputs}]


def locks():
    from hashlib import sha256
    paths = (Path(__file__), COLOMBIA, Path(runner.__file__), *(HERE.parents[1] / key for key in prior.locks()))
    return {str(path.relative_to(HERE.parents[1])): sha256(path.read_bytes()).hexdigest() for path in paths}


def replay(directory):
    from transformers import AutoTokenizer

    launch, finish = (prior.prior.load(directory / key) for key in ("launch.json", "complete.json"))
    trace, finals = (directory / name for name in ("transcript.jsonl", "final-records.json"))
    assert launch["sha256"] == locks() and finish["transcript_sha256"] == runner.digest(trace)
    assert finish["final_records_sha256"] == runner.digest(finals)
    rows = {row["id"]: row for row in map(json.loads, trace.read_text().splitlines())}
    wanted = {row["id"]: row for row in requests()}
    assert rows.keys() == wanted.keys() and len(rows) == finish["records"] == 76
    token = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = token.convert_tokens_to_ids("<|im_end|>")
    for key, prompt in wanted.items():
        row = rows[key]
        assert all(row[k] == value for k, value in prompt.items())
        assert runner.encode(token, prompt) == row["input_ids"]
        ids = row["output_ids"]
        assert 0 < len(ids) <= CAP and eos not in ids[:-1]
        assert row["ended"] == (ids[-1] == eos)
        assert row["output"] == token.decode(ids, skip_special_tokens=True).strip()
    assert prior.prior.load(finals) == {FAMILY: {key: row["output"] for key, row in rows.items()}}
    return rows


def normalized(row):
    if not row["ended"]:
        return "INVALID"
    text = row["output"]
    if text == "UNKNOWN":
        return None
    try:
        canonical = date.fromisoformat(text).isoformat()
        return canonical if canonical == text else "INVALID"
    except ValueError:
        return "INVALID"


def score(directory):
    rows = replay(directory)
    selected = {}
    assembled = {}
    for key, family, field, draft, card, correct, case_id, source_id in cases():
        got = normalized(rows[key])
        gated = got if card is not None else None
        selected[key] = {"family": family, "field": field, "draft": draft, "card": card,
                         "expected": correct, "observed": got, "gated": gated, "raw": rows[key]["output"]}
        if case_id is not None:
            handover = assembled.setdefault(case_id, {"id": case_id, "actions": {}, "deliverable": {}})
            handover["actions"][field] = ("verify" if gated is None else
                                           "invalid" if gated == "INVALID" else
                                           "confirm" if gated == prior.as_iso(draft) else "correct")
            # The scheduler accepts the ISO string. Match the historical grader's
            # pre-existing natural-date serialization for its comparison only.
            handover["deliverable"][field] = (date.fromisoformat(gated).strftime("%-d %B %Y")
                                                if gated and gated != "INVALID" else None)
            selected[key]["received_source_id"] = source_id if card is not None else None
    predictions = list(assembled.values())
    stats = {}
    for family in ("unami2023", "drc2023", "drc_control", "colombia"):
        group = [row for row in selected.values() if row["family"] == family]
        stats[family] = {"total": len(group), "raw_correct": sum(row["observed"] == row["expected"] for row in group),
                         "gated_correct": sum(row["gated"] == row["expected"] for row in group),
                         "expected_unknown": sum(row["expected"] is None for row in group),
                         "correct_unknown_raw": sum(row["expected"] is None and row["observed"] is None for row in group),
                         "correct_unknown_gated": sum(row["expected"] is None and row["gated"] is None for row in group)}
    return {"scope": "One bound-source field per call. The host performs absence referral and derives the action from the date. "
                     "This changes scope, input visibility, action factorization and number of calls compared with the earlier two-line writer.",
            "stats": stats, "historical_handover": prior.prior.grade_handovers.grade(predictions),
            "routing": prior.prior.downstream(predictions), "all_reads": selected, "predictions": predictions}


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
