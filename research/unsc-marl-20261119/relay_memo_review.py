"""Build an anonymous final-review deck and audit exact evidence spans."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

import relay_final_memo as experiment

ROOT=experiment.HERE
RUBRIC=experiment.relay.KIT/"relay-final-rubric.json"
INSTRUCTIONS=ROOT/"judge/instructions.md"


def verify(directory):
    import transformers
    from transformers import AutoTokenizer

    launch=experiment.read(directory/"launch.json")
    assert launch["sha256"]==experiment.sources()
    assert launch["transformers"]==transformers.__version__
    finished=experiment.read(directory/"complete.json")
    raw=directory/"memos.jsonl"
    assert finished["sha256"]==sha256(raw.read_bytes()).hexdigest()
    rows=list(map(json.loads,raw.read_text().splitlines()))
    by_id={r["id"]:r for r in rows}
    assert len(rows)==len(by_id)==finished["records"]
    assert len({r["inference_id"] for r in rows})==finished["unique_inferences"]
    tokenizer=AutoTokenizer.from_pretrained(launch["model"],local_files_only=True,padding_side="left")
    eos=tokenizer.convert_tokens_to_ids("<|im_end|>")
    for plan,row in zip(experiment.suite(),rows,strict=True):
        assert {k:row[k] for k in plan}==plan
        prefix=tokenizer.apply_chat_template(plan["messages"],tokenize=False,add_generation_prompt=True,
                                             enable_thinking=False)
        assert tokenizer.encode(prefix,add_special_tokens=False)==row["input_ids"]
        assert tokenizer.decode(row["output_ids"],skip_special_tokens=True).strip()==row["output"]
        assert (row["output_ids"][-1]==eos)==(row["stop"]=="eos")
        if row["stop"]=="cap":
            assert len(row["output_ids"])==experiment.CAP
        source=by_id[row["inference_id"]]
        assert all(source[k]==row[k] for k in ("messages","expected","input_ids","output_ids"))
    return rows


def terms(row,rubric,identifier):
    prompt=json.loads(row["messages"][1]["content"])
    status=prompt["checked_status"]
    cards=prompt["evidence_at_chair"]
    supplied={"context":prompt["workshop_fiction"],"rule":prompt["public_rule"],
              "checked":"Workshop status: "+status,**prompt["historical_evidence"]}
    for i, card in enumerate(cards,1):
        supplied[f"card-{i}"]=f"{card['owner']} has the workshop card {card['card']}."
    names=[name for name in prompt["possible_card_holders"] if name not in {c["owner"] for c in cards}]
    if names:
        assert len(names)==1
        supplied["missing"]=f"No workshop card was delivered from the {names[0]}."
    units=[]
    for unit in rubric["units"]:
        requirement=unit["required"]
        if isinstance(requirement,dict):
            requirement=requirement[row["family"]]
        units.append({**unit,"required":requirement})
    return {"id":identifier,"family":row["family"],"evidence":supplied,
            "candidate":row["output"],"units":units,"format":rubric["format"]}


def deck(directory):
    rows=verify(directory)
    rubric=experiment.read(RUBRIC)
    items,key={},{}
    for row in rows:
        fingerprint=sha256(("memo-review-v1/"+row["inference_id"]).encode()).hexdigest()[:10]
        key[row["id"]]=fingerprint
        if fingerprint not in items:
            items[fingerprint]=terms(row,rubric,fingerprint)
    return {"judge_protocol_sha256":sha256(INSTRUCTIONS.read_bytes()).hexdigest(),
            "rubric_sha256":sha256(RUBRIC.read_bytes()).hexdigest(),
            "deck":dict(sorted(items.items()))},key


def score(folder,judgments):
    blinded,key=deck(folder)
    restored=experiment.read(judgments)
    assert blinded["rubric_sha256"]==restored["rubric_sha256"]
    assert set(restored["reviews"])==set(blinded["deck"])
    table={}
    for ident,item in blinded["deck"].items():
        review=restored["reviews"][ident]
        assert set(review["units"])=={u["id"] for u in item["units"]}
        for mark in [*review["units"].values(),review["guard"]]:
            quote=mark["response"]
            assert isinstance(mark["reason"],str) and mark["reason"]
            assert not quote or quote in item["candidate"],(ident,quote)
            for evidence in mark["source"]:
                assert evidence["quote"] and evidence["quote"] in item["evidence"][evidence["block"]],evidence
            if mark["status"] in ("met","failed"):
                assert quote and mark["source"]
        statuses=Counter(mark["status"] for mark in review["units"].values())
        assert set(statuses)<=set(("met","unmet","uncertain"))
        assert review["guard"]["status"] in ("clear","failed","uncertain")
        words=len(item["candidate"].split())
        table[ident]={"score_min":7*statuses["met"],"score_max":7*(statuses["met"]+statuses["uncertain"]),
                      "units":dict(statuses),"words":words,"word_cap_pass":words<=100,
                      "exact_line":next(iter(item["candidate"].splitlines()),"")==item["evidence"]["checked"],
                      "guard":review["guard"]["status"]}
    return {"scope":restored["scope"],"unique_memos":len(table),"archive":{name:table[ident] for name,ident in key.items()}}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path)
    parser.add_argument("--judgments",type=Path)
    args=parser.parse_args()
    if args.judgments:
        print(json.dumps(score(args.directory,args.judgments),indent=2))
    else:
        catalog,key=deck(args.directory)
        (args.directory/"review-deck.json").write_text(json.dumps(catalog,indent=2)+"\n")
        (args.directory/"review-key.json").write_text(json.dumps(key,indent=2)+"\n")
