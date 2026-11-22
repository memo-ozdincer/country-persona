"""Check whether a frozen chair states the decisions warranted by truthful receipts."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

import three_seat_decision as game

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "benchmark-kit/validity-audit"))
import source_record_run as runner

ROOT = HERE / "three-seat-memo-evidence"
FAMILY = "three-seat-outer-space-memo"
VIEWS = (
    ("d_before", (0, 0), 0, None),
    ("d_with_reply", (0, 0), 0, 0),
    ("shared_before", (2, 0), 0, None),
    ("impasse_with_reply", (2, 0), 0, 2),
    ("f_with_reply", (2, 1), 0, 2),
    ("still_unresolved", (1, 2), 0, 2),
)
ROLES = ("First delegate", "Second delegate")


def requests():
    case = json.loads((HERE / "case.json").read_text())
    options = [r for r in case["options"] if r["id"] in game.PACKAGES]
    instruction = ("For this fictional workshop, use only verified receipts and the stated possible cards. "
                   "The three grades for a package come from the two delegates and the public third seat. "
                   "Exclude a package if any grade is zero. Rank the rest by their lowest grade, then by the "
                   "sum of all three grades, with higher better. For each compatible pair of private cards, "
                   "find the winning package set, or impasse when none is feasible. A definite recommendation "
                   "needs a common winner across every compatible pair, or verified impasse in every pair. "
                   "Otherwise give unresolved. First line must be exactly A, D, F, impasse or unresolved. "
                   "Then give the reason in at most 45 words, distinguishing what the receipts prove from what "
                   "could still change. These are fictional grades, separate from historical policy.")
    for name, world, a, b in VIEWS:
        receipts = [game.message(world, 0, a), game.message(world, 1, b) if b is not None else None]
        possible, warranted = game.verify(*receipts)
        texts = []
        for role, arrived in zip(ROLES, receipts, strict=True):
            if arrived is None:
                continue
            i, grade = arrived
            texts.append(f"{role}: I certify that my grade for package {game.PACKAGES[i]} is {grade}.")
        body = {"task": instruction, "package_order": game.PACKAGES, "workshop_options": options,
                "public_third_seat_grades": game.PUBLIC, "possible_private_cards": {
                    ROLES[0]: game.CARDS_A, ROLES[1]: game.CARDS_B}, "verified_receipts": texts}
        yield {"id": name, "cap": 100, "receipt_values": receipts, "possible": possible,
               "key": sorted(warranted) or ["unresolved"], "messages": [
                   {"role": "system", "content": "Write the chair's decision for this fictional UN drafting workshop."},
                   {"role": "user", "content": json.dumps(body)}]}


def episode(generate):
    return [{"family": FAMILY, "final": generate(list(requests()))}]


def locks():
    return {p.name: runner.digest(p) for p in (Path(__file__), Path(game.__file__), HERE / "case.json",
                                               Path(runner.__file__))}


def replay(directory):
    from transformers import AutoTokenizer

    launch, finish = [json.loads((directory / name).read_text()) for name in ("launch.json", "complete.json")]
    raw, finals = directory / "transcript.jsonl", directory / "final-records.json"
    assert launch["sha256"] == locks() and runner.digest(raw) == finish["transcript_sha256"]
    assert runner.digest(finals) == finish["final_records_sha256"]
    rows = {r["id"]: r for r in map(json.loads, raw.read_text().splitlines())}
    assert len(rows) == finish["records"] == len(VIEWS)
    tok = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    for wanted in requests():
        row = rows[wanted["id"]]
        assert all(row[k] == json.loads(json.dumps(v)) for k, v in wanted.items())
        assert runner.encode(tok, wanted) == row["input_ids"]
        ids = row["output_ids"]
        assert 0 < len(ids) <= row["cap"] and eos not in ids[:-1] and (ids[-1] == eos) == row["ended"]
        assert tok.decode(ids, skip_special_tokens=True).strip() == row["output"]
    assert json.loads(finals.read_text()) == {FAMILY: {k: r["output"] for k, r in rows.items()}}
    return rows


def score(directory):
    rows = []
    for r in replay(directory).values():
        decision, _, reason = r["output"].partition("\n")
        rows.append({"id": r["id"], "key": r["key"], "decision": decision, "correct": decision in r["key"],
                     "reason": reason.strip(), "finished": r["ended"], "legal_reason_length": len(reason.split()) <= 45})
    return {"scope": "Mechanically scored first line from six frozen Qwen responses. Receipts are faithfully rendered "
                     "from the simulated grades. The reason requires separate exact-span review.",
            "correct": sum(r["correct"] for r in rows), "records": rows}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "score"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, episode=episode, locks=locks):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps(score(args.directory), indent=2))
