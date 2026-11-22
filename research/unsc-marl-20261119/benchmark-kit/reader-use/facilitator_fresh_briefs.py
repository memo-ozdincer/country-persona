"""Generate chair records from received source cards and compare frozen dispositions."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_source_relation as judge
import facilitator_replacement as writing

HERE = judge.HERE
transfer = judge.prior.witness.transfer
base = transfer.base
load = judge.protocol.delivery.load
runner = writing.runner
EVIDENCE = HERE / "facilitator-source-relation-evidence/results.json"
QUOTE = judge.prior.routing.ARTIFACT
PANELS = (("unifil", 0), ("unifil", 3), ("colombia", 0), ("colombia", 1))
MODES = ("pooled", "quote", "agreement")
FAMILY = "facilitator-fresh-briefs"
CAP = 104
TASK = writing.TASK + (
    " Report the precise supported position and its qualification. Insufficient evidence for a speaker must remain "
    " unverified. The facilitator brief records documentary positions and does not authorize any Council action."
)


def fixtures():
    quotes = load(QUOTE)["reads"]
    verdicts = load(EVIDENCE)["decisions"]
    packets = transfer.packets()
    for family, number in PANELS:
        proposal, _, truth = transfer.PANELS[family][number]
        keys = [f"{family}/{number}/{slot}" for slot in range(2)]
        quoted = tuple(quotes[key]["admitted"] for key in keys)
        judged = tuple(verdicts.get(f"routed/{key}", {}).get("stable_relation", "unknown") for key in keys)
        agreed = tuple(a if a == b else "unknown" for a, b in zip(quoted, judged, strict=True))
        for mask, flags in enumerate(product((False, True), repeat=2)):
            seen = frozenset(i for i, bit in enumerate(flags) if bit)
            tags = {f"S{i+1}": packets[family][i][1] for i in sorted(seen)}
            yield (f"{family}-{number}/{mask}", proposal, tags, truth, seen,
                   {"pooled": None, "quote": base.decision(quoted, seen),
                    "agreement": base.decision(agreed, seen)}, {"quote": quoted, "agreement": agreed})


def request_id(key, action):
    return f"{key}/{action or 'pooled'}"


def requests():
    for key, proposal, tags, _, _, variants, _ in fixtures():
        for action in dict.fromkeys(variants.values()):
            payload = {"proposed_sentence": proposal, "documentary_passages": tags}
            wording = TASK
            if action is not None:
                payload["checked_disposition"] = action
                wording += (" Use the supplied disposition for the heading. Cite only documentary passages. "
                            "Flag an evidence gap in the sentence if the received passages cannot establish a position.")
            yield {"id": request_id(key, action), "cap": CAP, "messages": [
                {"role": "system", "content": wording},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ]}


def episode(generate):
    incoming = list(requests())
    records = {}
    for start in range(0, len(incoming), 12):
        records.update(generate(incoming[start:start+12]))
    return [{"family": FAMILY, "final": records}]


def pins():
    files = [Path(__file__), Path(writing.__file__), Path(runner.__file__), EVIDENCE, QUOTE,
             *(HERE.parents[1] / file for file in judge.pins())]
    return {str(p.resolve().relative_to(HERE.parents[1])): sha256(p.read_bytes()).hexdigest() for p in files}


def rows(directory):
    from transformers import AutoTokenizer

    launch, finish = (load(directory / name) for name in ("launch.json", "complete.json"))
    raw, final = (directory / name for name in ("transcript.jsonl", "final-records.json"))
    assert launch["sha256"] == pins() and finish["transcript_sha256"] == runner.digest(raw)
    assert finish["final_records_sha256"] == runner.digest(final)
    token = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = token.convert_tokens_to_ids("<|im_end|>")
    captured = {row["id"]: row for row in map(json.loads, raw.read_text().splitlines())}
    assert captured.keys() == {r["id"] for r in requests()} and len(captured) == finish["records"]
    for expected in requests():
        row = captured[expected["id"]]
        assert all(row[k] == v for k, v in expected.items())
        assert runner.encode(token, expected) == row["input_ids"]
        ids = row["output_ids"]
        assert 0 < len(ids) <= CAP and eos not in ids[:-1]
        assert row["ended"] == (ids[-1] == eos) and row["output"] == token.decode(ids, skip_special_tokens=True).strip()
    assert load(final) == {FAMILY: {key: row["output"] for key, row in captured.items()}}
    return captured


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("run", "replay"))
    p.add_argument("directory", type=Path)
    p.add_argument("--model", type=Path)
    args = p.parse_args()
    if args.mode == "run":
        with patch.multiple(runner, episode=episode, locks=pins):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps({"verified_generations": len(rows(args.directory))}))
