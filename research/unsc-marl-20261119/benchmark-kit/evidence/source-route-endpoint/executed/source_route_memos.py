"""Test all four qualification deliveries in the Sudan chair's final record."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import source_record_run as runner
from source_record_compact import FINAL
from source_record_episode import PACK
from source_route_fit import CASE

HERE = Path(__file__).resolve().parent
FIT = HERE.parent/"evidence/source-route-fit/fit.json"


def suite():
    case = json.loads(CASE.read_text())
    protocol = json.loads(PACK.read_text())["protocol"]
    fit = json.loads(FIT.read_text())
    assert fit["case_sha256"] == sha256(CASE.read_bytes()).hexdigest()
    relevant = [row for row in fit["sudan"] if row["public"] == ["RU-A", "CN-A"]]
    state, = relevant
    assert state["arms"]["learned"]["sent"] == ["RU-B", "CN-B"]
    assert state["arms"]["independent"]["sent"] == [None, None]
    published = {**case["docket"], **{code: claim for portfolio in case["delegate_evidence"].values()
                                     for code, claim in portfolio.items() if code in state["public"]}}
    private = {code: claim for portfolio in case["delegate_evidence"].values()
               for code, claim in portfolio.items() if code not in published}
    for name, extra in (("no_qualifications", ()), ("russian_only", ("RU-B",)),
                        ("chinese_only", ("CN-B",)), ("both_qualifications", ("RU-B", "CN-B"))):
        packet = {**published, **{key: private[key] for key in extra}}
        payload = {"task": protocol["shared_task"] + " " + FINAL,
                   "evidence": packet, "working_text": []}
        yield {"id": f"{case['family']}/{name}/chair", "evidence_ids": list(packet), "seen": [],
               "cap": protocol["generation_ceiling"]["chair"],
               "messages": [
                   {"role":"system","content":"You are a neutral historical record writer. The dated evidence is the only factual authority."},
                   {"role":"user","content":json.dumps(payload,ensure_ascii=False)},
               ]}


def episode(generate):
    batch = list(suite())
    return [{"family":batch[0]["id"].split("/")[0],"final":generate(batch)}]


def locks():
    paths = (Path(__file__).resolve(), Path(runner.__file__), Path(__file__).with_name("source_record_compact.py"),
             CASE, PACK, FIT)
    return {str(p.relative_to(HERE.parent)): sha256(p.read_bytes()).hexdigest() for p in paths}


def replay(directory, expected_records=4):
    from transformers import AutoTokenizer
    launch = json.loads((directory/"launch.json").read_text())
    raw = directory/"transcript.jsonl"
    complete = json.loads((directory/"complete.json").read_text())
    assert launch["sha256"] == locks()
    assert complete["transcript_sha256"] == runner.digest(raw)
    tokenizer = AutoTokenizer.from_pretrained(launch["model"],local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    results = {}
    for expected,row in zip(suite(), map(json.loads,raw.read_text().splitlines()),strict=True):
        assert all(row[k] == v for k,v in expected.items())
        assert row["input_ids"] == runner.encode(tokenizer,expected)
        numbers = row["output_ids"]
        assert 0 < len(numbers) <= expected["cap"] and eos not in numbers[:-1]
        assert (numbers[-1] == eos) == row["ended"]
        assert tokenizer.decode(numbers,skip_special_tokens=True).strip() == row["output"]
        results[row["id"]] = row["output"]
    finals = directory/"final-records.json"
    assert complete["final_records_sha256"] == runner.digest(finals)
    assert results == next(iter(json.loads(finals.read_text()).values()))
    assert len(results) == complete["records"] == expected_records
    return {"records": expected_records, "exact_replay": True}


if __name__=="__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode",choices=("run","replay","check"))
    cli.add_argument("directory",type=Path,nargs="?")
    cli.add_argument("--model",type=Path)
    args=cli.parse_args()
    if args.mode=="run":
        if args.model is None or args.directory is None:
            cli.error("--model and directory are required")
        with patch.object(runner,"episode",new=episode), patch.object(runner,"locks",new=locks):
            runner.run(args.model,args.directory)
    elif args.mode=="replay":
        print(json.dumps(replay(args.directory),indent=2))
    else:
        print(json.dumps([{"id":r["id"],"sources":r["evidence_ids"]} for r in suite()],indent=2))
