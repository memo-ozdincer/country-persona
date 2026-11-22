"""Generate complete facilitator replacements under evidence and disposition interventions."""
import argparse
from pathlib import Path
import json
import sys
from unittest.mock import patch

import routed_common_ground as prior

HERE = prior.HERE
sys.path.insert(0, str(HERE.parent / "validity-audit"))
import source_record_run as runner

SCORED = HERE / "routed-common-ground-evidence/results.json"
ARMS = ("direct", "staged")
FAMILY = "facilitator-replacement"
CAP = 92
TASK = (
    "Prepare the final facilitator brief. Return one line with the disposition retain, revise, or withhold, "
    "then a vertical bar, then a replacement sentence of at most 48 words. "
    "Retain only if both sides are documented. Revise if an available source contradicts the claim. "
    "Otherwise withhold. Preserve any documented side of the claim, mark unverified sides as such, "
    "and attach the exact bracketed passage ID to each substantive attribution. "
    "With no supporting passages state the evidence is insufficient. "
    "A government position, an adopted act, a vote and a financial pledge are distinct."
)


def requests():
    saved = {r["id"]: r for r in prior.delivery.load(SCORED)["rows"]}
    for row in prior.inputs()["inputs"]:
        assert saved[row["id"]]["proposal"] == row["proposed_sentence"]
        for arm in ARMS:
            payload = {"proposed_sentence": row["proposed_sentence"], "documentary_passages": row["sources"]}
            wording = TASK
            if arm == "staged":
                payload["checked_disposition"] = saved[row["id"]]["separate"]
                wording += " Use the supplied disposition. It supplies no evidence for an individual speaker."
            yield {"id": f"{row['id']:02}/{arm}", "cap": CAP, "messages": [
                {"role": "system", "content": wording},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ]}


def episode(generate):
    wanted = list(requests())
    rows = {}
    for i in range(0, len(wanted), 16):
        rows.update(generate(wanted[i:i+16]))
    return [{"family": FAMILY, "final": rows}]


def locks():
    from hashlib import sha256
    files = (Path(__file__), SCORED, Path(runner.__file__), *(HERE.parents[1] / key for key in prior.hashes()))
    return {str(p.relative_to(HERE.parents[1])): sha256(p.read_bytes()).hexdigest() for p in files}


def replay(directory):
    from transformers import AutoTokenizer

    launch, finish = (prior.delivery.load(directory / name) for name in ("launch.json", "complete.json"))
    raw, finals = (directory / name for name in ("transcript.jsonl", "final-records.json"))
    assert launch["sha256"] == locks() and finish["transcript_sha256"] == runner.digest(raw)
    assert finish["final_records_sha256"] == runner.digest(finals)
    token = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = token.convert_tokens_to_ids("<|im_end|>")
    rows = {row["id"]: row for row in map(json.loads, raw.read_text().splitlines())}
    assert len(rows) == finish["records"] == 48
    for expected in requests():
        record = rows[expected["id"]]
        assert all(record[k] == v for k, v in expected.items())
        assert runner.encode(token, expected) == record["input_ids"]
        ids = record["output_ids"]
        assert 0 < len(ids) <= CAP and eos not in ids[:-1]
        assert record["ended"] == (ids[-1] == eos) and record["output"] == token.decode(ids, skip_special_tokens=True).strip()
    assert prior.delivery.load(finals) == {FAMILY: {key: row["output"] for key, row in rows.items()}}
    return rows


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "replay"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, episode=episode, locks=locks):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps({"verified_generations": len(replay(args.directory))}))
