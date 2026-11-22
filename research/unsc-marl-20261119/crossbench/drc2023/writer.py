"""First-pass DRC writing with packet-bound citations and matched output caps."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "benchmark-kit/validity-audit"))
import source_record_run as runner

CASE = HERE / "case.json"
FIELDS = {
    "SANCTIONS": "Give the renewed measures, their end date and where the 1807 measure continues to apply. Use up to 31 words.",
    "EXPERTS": "Give the mandate expiry and intended review date separately. Include the dates and Council recipient for the two reports, and the separate Committee updates and exceptions. Use up to 50 words.",
    "RUSSIA": "Give its vote and grounds for reviewing unsuitable sanctions, its view on illegitimate unilateral measures and its account of when the earlier notification requirement was lifted. Use up to 43 words.",
    "DRC": "Give the affected state's welcome for the targets of the renewed measures and its separate cooperation, objectivity and submitted-report points. Use up to 38 words.",
    "overlap": "In up to 27 words state common ground and give the separate vote or speaking role for each party.",
}
PACKETS = {
    "with_russia": ["SANCTIONS", "EXPERTS", "RUSSIA"],
    "with_drc": ["SANCTIONS", "EXPERTS", "DRC"],
    "both_positions": ["SANCTIONS", "RUSSIA", "DRC"],
}
SYSTEM = "Write archival Council summaries using the supplied documentary facts."


def row(name, sources, payload, cap, variant):
    return {"id": name, "cap": cap, "evidence_ids": sources, "variant": variant, "messages": [
        {"role": "system", "content": SYSTEM}, {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]}


def build():
    data = json.loads(CASE.read_text())
    out = []
    for label, instruction in FIELDS.items():
        comparison = label == "overlap"
        scope = ["VOTE", "RUSSIA", "DRC"] if comparison else [label]
        material = data["comparison"] if comparison else data["sources"][label]
        out.append(row(label, scope, {"task": "Write just this field. The record renderer supplies its source IDs. "
                       "Keep each actor and date attached to its own action. " + instruction,
                       "evidence": material}, 104, "field"))
    for name, ids in PACKETS.items():
        compare = {"RUSSIA", "DRC"} <= set(ids)
        payload = {"task": "Write the complete supplement in at most 155 words, with no heading or concluding filler. "
                   "The roll call is already written. Keep each legal act, expiry date, institutional recipient, "
                   "and delegated statement distinct. Give exact bracketed IDs for factual claims.",
                   "evidence": {k: data["sources"][k] for k in ids}}
        if compare:
            payload["comparison"] = data["comparison"]
        out.append(row(name, ids, payload, 104 * (len(ids) + compare), "whole"))
    return out


def episode(generate):
    batches = defaultdict(list)
    for request in build():
        batches[request["cap"]].append(request)
    final = {}
    for batch in batches.values():
        final.update(generate(batch))
    return [{"family": "drc-writer-first-pass", "final": final}]


def locks():
    return {f.name: runner.digest(f) for f in (CASE, Path(__file__), Path(runner.__file__),
                  HERE / "reference.json", HERE / "acceptance.json")}


def replay(directory):
    from transformers import AutoTokenizer

    launch, complete = [json.loads((directory / f).read_text()) for f in ("launch.json", "complete.json")]
    trace = directory / "transcript.jsonl"
    final = directory / "final-records.json"
    assert launch["sha256"] == locks() and complete["transcript_sha256"] == runner.digest(trace)
    assert complete["final_records_sha256"] == runner.digest(final)
    records = {r["id"]:r for r in map(json.loads, trace.read_text().splitlines())}
    texts = json.loads(final.read_text())["drc-writer-first-pass"]
    assert len(records) == len(texts) == complete["records"] == len(build()) == 8
    tok = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    for request in build():
        recorded = records[request["id"]]
        assert all(recorded[k] == v for k, v in request.items())
        assert recorded["input_ids"] == runner.encode(tok, request)
        ids = recorded["output_ids"]
        assert 0 < len(ids) <= request["cap"] and eos not in ids[:-1] and recorded["ended"] == (ids[-1] == eos)
        assert texts[request["id"]] == recorded["output"] == tok.decode(ids, skip_special_tokens=True).strip()
    return records


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("check", "run", "replay"))
    cli.add_argument("directory", nargs="?", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "check":
        print(json.dumps({r["id"]:r["cap"] for r in build()}))
    elif args.mode == "run":
        with patch.multiple(runner, episode=episode, locks=locks):
            runner.run(args.model, args.directory)
    else:
        print(json.dumps({"replayed": len(replay(args.directory)), "exact": True}))
