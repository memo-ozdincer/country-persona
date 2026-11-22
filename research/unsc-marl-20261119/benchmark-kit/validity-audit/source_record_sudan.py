"""Run a source-record transfer to the frozen Sudan meeting and draft."""
import argparse
from contextlib import contextmanager
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import source_record_run as runner
import source_record_episode as protocol
from source_record_compact import FINAL, REVISION

CASE = Path(__file__).with_name("source-record-sudan-reserve.json")


def pack():
    original = json.loads(protocol.PACK.read_text())
    return {**original, "cases": [json.loads(CASE.read_text())]}


def episode(generate):
    # Freeze the same episode graph, with the compact source/citation prompts
    # imposed on every reviser and final chair. The new family has fresh openings.
    source_pack = pack()
    class Packet:
        def read_text(self):
            return json.dumps(source_pack)
    def adapt(batch):
        prompts = []
        for row in batch:
            phase = row["id"].rsplit("/", 1)[-1]
            if phase.startswith("opening_"):
                prompts.append(row)
                continue
            original_messages = row["messages"]
            old = json.loads(original_messages[-1]["content"])
            instructions = REVISION if phase.startswith("revision_") else old["task"] + " " + FINAL
            role = original_messages[0]["content"].split(". Use the supplied", 1)[0]
            content = {"task": instructions, "evidence": old["evidence"],
                       "working_text": [{"type": "provisional working text", "text": x["text"]} for x in old["drafts"]]}
            messages = [{"role": "system", "content": role + ". The dated evidence is the only factual authority."},
                        {"role": "user", "content": json.dumps(content, ensure_ascii=False)}]
            prompts.append({**row, "messages": messages})
        return generate(prompts)
    with patch.object(protocol, "PACK", new=Packet()):
        return protocol.episode(adapt)


def locks():
    files = (CASE, protocol.PACK, Path(__file__).resolve(), Path(protocol.__file__),
             Path(runner.__file__), Path(__file__).with_name("source_record_compact.py"))
    return {f.name: sha256(f.read_bytes()).hexdigest() for f in files}


def replay(folder):
    from transformers import AutoTokenizer
    launch=json.loads((folder/"launch.json").read_text())
    raw=folder/"transcript.jsonl"
    complete=json.loads((folder/"complete.json").read_text())
    assert launch["sha256"] == locks()
    assert complete["transcript_sha256"] == runner.digest(raw)
    by_id={r["id"]:r for r in map(json.loads,raw.read_text().splitlines())}
    tok=AutoTokenizer.from_pretrained(launch["model"],local_files_only=True)
    eos=tok.convert_tokens_to_ids("<|im_end|>")
    def read(batch):
        result={}
        for plan in batch:
            r=by_id.pop(plan["id"])
            assert all(r[k] == json.loads(json.dumps(val)) for k,val in plan.items())
            assert r["input_ids"] == runner.encode(tok, plan)
            ids=r["output_ids"]
            assert 0 < len(ids) <= r["cap"] and eos not in ids[:-1]
            assert (ids[-1] == eos) == r["ended"]
            assert tok.decode(ids,skip_special_tokens=True).strip() == r["output"]
            result[r["id"]]=r
        return result
    results=episode(read)
    assert not by_id and complete["records"]==13
    finals={row["family"]:{k:v["output"] for k,v in row["final"].items()} for row in results}
    assert finals == json.loads((folder/"final-records.json").read_text())
    assert complete["final_records_sha256"] == runner.digest(folder/"final-records.json")
    return {"records":13,"final_records":3,"exact_replay":True}


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode",choices=("run","replay","check"))
    cli.add_argument("directory",type=Path,nargs="?")
    cli.add_argument("--model",type=Path)
    args=cli.parse_args()
    if args.mode=="run":
        if args.model is None or args.directory is None:
            cli.error("--model and directory are required for run")
        with patch.object(runner,"episode",new=episode), patch.object(runner,"locks",new=locks):
            runner.run(args.model,args.directory)
    elif args.mode=="replay":
        print(json.dumps(replay(args.directory),indent=2))
    else:
        def fake(batch):
            return {r["id"]:{**r,"output":"Standing in for a local model response."} for r in batch}
        result=episode(fake)[0]
        print(json.dumps({"family": result["family"], "counts": {k:len(result[k]) for k in ("openings","revisions","final")}},indent=2))
