"""Run frozen local readers, field writers and matched packet synthesizers on two new meetings."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_bound_fields as fields
import facilitator_fresh_briefs as chair
import facilitator_source_relation as judge
import facilitator_witness as witness

HERE = chair.HERE
PACK = HERE / "facilitator-transfer-panels.json"
runner = chair.runner
base = chair.base
FAMILY = "facilitator-event-transfer"


def panels():
    for family, docket in chair.load(PACK).items():
        for index, (claim, predicate, truth, _) in enumerate(docket["proposals"]):
            yield f"{family}-{index}", claim, predicate, tuple(truth), docket["sources"]


def prompt(key, cap, task, payload):
    return {"id": key, "cap": cap, "messages": [
        {"role": "system", "content": task},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]}


def local():
    witness_task = witness.requests()[0]["messages"][0]["content"]
    for panel, claim, predicate, _, sources in panels():
        for i, (speaker, source) in enumerate(sources, 1):
            key = f"{panel}/S{i}"
            payload = {"speaker": speaker, "proposed_joint_statement": claim, "source": source}
            yield prompt(f"{key}/field", fields.CAP, fields.TASK, payload)
            yield prompt(f"{key}/witness", witness.CAP, witness_task, {"claim": f"{speaker} {predicate}.", "source": source})


def packets():
    for panel, claim, _, truth, cards in panels():
        for mask, flags in enumerate(product((False, True), repeat=2)):
            seen = frozenset(i for i, present in enumerate(flags) if present)
            sources = {f"S{i+1}": cards[i][1] for i in sorted(seen)}
            yield f"{panel}/{mask}", claim, truth, seen, sources, cards


def opinions(rows):
    out = {}
    for panel, _, predicate, _, cards in panels():
        for i, (speaker, source) in enumerate(cards, 1):
            key = f"{panel}/S{i}"
            row = rows[f"{key}/witness"]
            _, vote, span = witness.read_witness(row["output"], source) if row["ended"] else (None, "unknown", None)
            out[key] = vote, span, f"{speaker} {predicate}.", source
    return out


def audits(rows):
    for key, (vote, span, claim, source) in opinions(rows).items():
        if vote == "unknown":
            continue
        payload = {"quoted_premise": span, "passage_for_references": source, "assertion": claim}
        for item in judge.protocol.encoded((key,), judge.TASK, payload, judge.OPTIONS):
            which = item["observation"][-1]
            yield {"id": f"{key}/judge{which}", "cap": 4, "messages": item["messages"]}


def syntheses(rows):
    for packet, claim, _, seen, sources, _ in packets():
        panel, _ = packet.rsplit("/", 1)
        payload = {"proposed_sentence": claim, "documentary_passages": sources}
        yield prompt(f"{packet}/pooled", chair.CAP, chair.TASK, payload)
        notes = {f"S{i+1}": rows[f"{panel}/S{i+1}/field"]["output"] for i in sorted(seen)}
        if notes:
            task = chair.TASK + " Independent desk drafts may help organize the brief. Verify them against their source."
            yield prompt(f"{packet}/independent", chair.CAP, task, payload | {"independent_drafts": notes})


def plan(generate):
    rows = {}
    for tag in ("field", "witness"):
        rows.update(generate([r for r in local() if r["id"].endswith("/" + tag)]))
    judges = list(audits(rows))
    if judges:
        rows.update(generate(judges))
    wanted = list(syntheses(rows))
    for n in range(0, len(wanted), 14):
        rows.update(generate(wanted[n:n+14]))
    return [{"family": FAMILY, "final": rows}]


def pins():
    files = [Path(__file__), PACK, Path(fields.__file__), *(HERE.parents[1] / p for p in chair.pins())]
    return {str(p.resolve().relative_to(HERE.parents[1])): sha256(p.read_bytes()).hexdigest() for p in files}


def read(directory):
    from transformers import AutoTokenizer

    launch, finish = (chair.load(directory / name) for name in ("launch.json", "complete.json"))
    raw, final = (directory / name for name in ("transcript.jsonl", "final-records.json"))
    assert launch["sha256"] == pins() and finish["transcript_sha256"] == runner.digest(raw)
    assert finish["final_records_sha256"] == runner.digest(final)
    token = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = token.convert_tokens_to_ids("<|im_end|>")
    rows = {row["id"]: row for row in map(json.loads, raw.read_text().splitlines())}
    prompts = [*local(), *audits(rows), *syntheses(rows)]
    assert rows.keys() == {row["id"] for row in prompts} and len(rows) == finish["records"] == len(prompts)
    for expected in prompts:
        row = rows[expected["id"]]
        assert all(row[k] == v for k, v in expected.items())
        assert runner.encode(token, expected) == row["input_ids"]
        ids = row["output_ids"]
        assert 0 < len(ids) <= expected["cap"] and eos not in ids[:-1]
        assert row["ended"] == (ids[-1] == eos) and row["output"] == token.decode(ids, skip_special_tokens=True).strip()
    assert chair.load(final) == {FAMILY: {key: row["output"] for key, row in rows.items()}}
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "verify"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--model", type=Path)
    args = parser.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, episode=plan, locks=pins):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps({"verified_generations": len(read(args.directory))}))
