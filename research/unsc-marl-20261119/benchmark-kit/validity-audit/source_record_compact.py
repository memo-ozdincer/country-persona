"""Run the compact, source-cited revision control on the frozen shared openings."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import source_record_run as original
from source_record_episode import PACK

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / "evidence/source-record-pilot"
ARMS = ("independent_drafts", "interactive")
REVISION = (
    "Return two short evidence-cited sentences, at most 45 words total. State the most consequential "
    "delegation position and one qualification, correction, or unresolved issue. Omit headings and "
    "introductory text. A draft can point you to a source to check. Cite only the supplied evidence IDs. "
    "Treat the draft as unverified and do not assert claims absent from your evidence."
)
FINAL = (
    "Use only the supplied evidence IDs as citations. The revisions are suggestions and their IDs "
    "are not source citations. Preserve the actual force of recorded words and actions. "
    "Label any analytical next step as your suggestion and attribute it to no historical speaker."
)


def frozen_openings():
    source = BASE / "transcript.jsonl"
    old = json.loads((BASE / "complete.json").read_text())
    assert sha256(source.read_bytes()).hexdigest() == old["transcript_sha256"]
    return {r["id"]: r for r in map(json.loads, source.read_text().splitlines()) if "/common/opening_" in r["id"]}


def episode(generate):
    openings = frozen_openings()
    pack = json.loads(PACK.read_text())
    caps = pack["protocol"]["generation_ceiling"]
    results = []
    for case in pack["cases"]:
        family = case["family"]
        docket = case["docket"]
        portfolio = case["delegate_evidence"]
        roles = tuple(portfolio)
        evidence = {**docket, **{k: v for p in portfolio.values() for k, v in p.items()}}
        def request(arm, phase, role, sources, histories, instruction):
            items = [{"type":"provisional working text", "text": item["output"]} for item in histories]
            return {"id": f"{family}/{arm}/{phase}", "evidence_ids": tuple(sources),
                    "seen": tuple(item["id"] for item in histories), "cap": caps[phase],
                    "messages": [
                        {"role": "system", "content": f"You are {role}. The dated evidence is the only factual authority."},
                        {"role": "user", "content": json.dumps({"task": instruction, "evidence": sources,
                                                                 "working_text": items}, ensure_ascii=False)},
                    ]}
        plans = []
        for arm in ARMS:
            for i, role in enumerate(roles, 1):
                own = openings[f"{family}/common/opening_{i}"]
                peer = openings[f"{family}/common/opening_{3-i}"]
                history = (own,) if arm == "independent_drafts" else (own, peer)
                plans.append(request(arm, f"revision_{i}", f"an analyst of the {role}'s position",
                                     {**docket, **portfolio[role]}, history, REVISION))
        revised = generate(plans)
        final = [request(arm, "chair", "a neutral historical record writer", evidence,
                         tuple(revised[f"{family}/{arm}/revision_{i}"] for i in (1, 2)),
                         pack["protocol"]["shared_task"] + " " + FINAL) for arm in ARMS]
        results.append({"family": family, "final": generate(final)})
    return results


def locks():
    files = (Path(__file__).resolve(), Path(original.__file__), PACK, BASE / "transcript.jsonl", BASE / "complete.json")
    return {p.name: sha256(p.read_bytes()).hexdigest() for p in files}


def replay(directory):
    from transformers import AutoTokenizer
    launch = json.loads((directory / "launch.json").read_text())
    complete = json.loads((directory / "complete.json").read_text())
    path = directory / "transcript.jsonl"
    assert launch["sha256"] == locks()
    assert complete["transcript_sha256"] == original.digest(path)
    records = {r["id"]: r for r in map(json.loads, path.read_text().splitlines())}
    tokenizer = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    def generate(batch):
        output = {}
        for request in batch:
            r = records.pop(request["id"])
            assert all(r[key] == json.loads(json.dumps(v)) for key, v in request.items())
            assert original.encode(tokenizer, request) == r["input_ids"]
            new = r["output_ids"]
            assert 0 < len(new) <= r["cap"] and eos not in new[:-1]
            assert tokenizer.decode(new, skip_special_tokens=True).strip() == r["output"]
            assert r["ended"] == (new[-1] == eos)
            output[r["id"]] = r
        return output
    out = episode(generate)
    assert not records and complete["records"] == 12
    finals = {record["family"]: {k: v["output"] for k, v in record["final"].items()} for record in out}
    assert json.loads((directory/"final-records.json").read_text()) == finals
    assert complete["final_records_sha256"] == original.digest(directory / "final-records.json")
    return {"records": complete["records"], "final_records": sum(map(len, finals.values())),
            "exact_prompt_and_output_replay": True}


def check():
    def generate(batch):
        return {r["id"]: {**r, "output": "First claim [VOTE]. Second claim [TEXT]."} for r in batch}
    trials = episode(generate)
    for case in trials:
        outputs = list(case["final"].values())
        assert outputs[0]["evidence_ids"] == outputs[1]["evidence_ids"]
        assert outputs[0]["cap"] == outputs[1]["cap"] == 256
    return {"case_families": [r["family"] for r in trials], "model_calls": 0}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "replay", "check"))
    cli.add_argument("directory", type=Path, nargs="?")
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        if args.model is None or args.directory is None:
            cli.error("--model and directory are required for run")
        with patch.object(original, "episode", new=episode), patch.object(original, "locks", new=locks):
            original.run(args.model, args.directory)
    elif args.mode == "replay":
        print(json.dumps(replay(args.directory), indent=2))
    else:
        print(json.dumps(check(), indent=2))
