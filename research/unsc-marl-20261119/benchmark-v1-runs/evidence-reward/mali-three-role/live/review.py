"""Rebuild, verify and grade the live three-role Mali dialogues."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import live

HERE=Path(__file__).resolve().parent
RUN=HERE/"evidence"
E,game=live.E,live.game
HISTORY=(
    "On 30 August 2023, France and the UAE’s draft S/2023/638 proposed extending sanctions and expert monitoring. "
    "It failed 13–1–1 because Russia, a permanent member, voted against. "
    "Russia’s separate S/2023/639 proposed a final sanctions extension and immediate dissolution of the Panel of Experts. "
    "It failed 1–1–13 for insufficient affirmative votes. "
    "The co-penholders sought to support the peace agreement and an orderly drawdown. "
    "Russia said the existing approach failed to address Mali’s transitional Government’s concerns."
)
AUTHORITY="Neither draft was adopted. The fictional workshop creates no authority over sanctions or expert mandates."


def rows(name):
    return [json.loads(line) for line in (RUN/name).read_text().splitlines()]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def verify():
    from jinja2.sandbox import ImmutableSandboxedEnvironment
    from tokenizers import Tokenizer

    hashes=E.read(RUN/"complete.json")
    assert set(hashes)=={"episodes.jsonl","tokens.jsonl","launch.json","loop-lock.json"}
    assert all(digest(RUN/name)==value for name,value in hashes.items())
    assert live.pins()==E.read(RUN/"loop-lock.json")
    launch=E.read(RUN/"launch.json")
    model=Path(launch["checkpoint"])
    assert digest(model/"model.safetensors.index.json")==launch["checkpoint_index_sha256"]
    assert launch["optimizer_updates"]==0
    assert launch["gpu_name"]=="NVIDIA RTX PRO 6000 Blackwell Server Edition"
    t=Tokenizer.from_file(str(model/"tokenizer.json"))
    template=ImmutableSandboxedEnvironment(trim_blocks=True,lstrip_blocks=True).from_string(
        (model/"chat_template.jinja").read_text())
    events=rows("episodes.jsonl")
    raw=iter([step for item in events for step in item["steps"]])
    receipts=iter(rows("tokens.jsonl"))
    eos=t.token_to_id("<|im_end|>")

    def observed(request):
        step,trace=next(raw),next(receipts)
        assert request==step["request"] and step["reply"]==trace["response"]
        content=template.render(messages=request["messages"],add_generation_prompt=True,
                                enable_thinking=False,tools=None)
        tokens=t.encode(content,add_special_tokens=False).ids
        assert tokens==trace["input_ids"] and len(tokens)==step["reply"]["input_tokens"]
        out=trace["output_ids"]
        assert out and len(out)==step["reply"]["output_tokens"]<=request["max_output_tokens"]
        assert eos not in out[:-1] and (out[-1]==eos)==(step["reply"]["termination"]=="complete")
        assert t.decode(out,skip_special_tokens=True).strip()==step["reply"]["text"]
        return step["reply"]

    assert json.loads(json.dumps(list(live.execute(observed))))==events
    assert next(raw,None) is None and next(receipts,None) is None
    return {"verified_worlds":len(events),"verified_live_replies":sum(len(x["steps"]) for x in events),
            "optimizer_updates":0,"tokenizer_sha256":digest(model/"tokenizer.json")}


def describe(case,option):
    return ", ".join(f"{r['field']} {r['values'][v]}" for r,v in zip(case["roles"],option,strict=True))


def public_conditions(case,state):
    return " ".join(f"The {r['name']} requires {r['field']} {r['values'][bit]}." if bit>=0
                    else f"The {r['name']}'s requirement remains unknown."
                    for r,bit in zip(case["roles"],state,strict=True))


def render(case,menu,state):
    decision,_=game.terminal(menu,state)
    conditions=public_conditions(case,state)
    if decision=="UNRESOLVED":
        workshop="The public signs establish neither a compatible option nor an impasse."
    elif decision=="IMPASSE":
        clauses=[]
        for i,(desk,bit) in enumerate(zip(case["roles"],state,strict=True)):
            if bit>=0:
                impossible=[label for label,option in case["packages"].items() if option[i]!=bit]
                clauses.append(f"The {desk['name']} excludes {', '.join(impossible)}.")
        workshop=" ".join(clauses)+" Together these exclusions cover the entire menu."
    else:
        workshop=f"Package {decision} is compatible with all three requirements: {describe(case,case['packages'][decision])}."
    return f"Decision: {decision}\n\nHistorical record. {HISTORY}\n\nFictional workshop. {conditions} {workshop}\n\n{AUTHORITY}"


def deck():
    config,menu,_,_=live.design()
    documents=E.read(live.BENCH/config["evidence"])["evidence"]
    public=documents+[{"id":"scope","text":config["scope"]},{"id":"menu",
                      "text":" ".join(f"{name}: {describe(config,option)}." for name,option in config["packages"].items())}]
    cases={}
    for episode in rows("episodes.jsonl"):
        truth=episode["evaluator_world"]
        private=[[{"id":f"card-{i}","text":f"The {r['name']} requires {r['field']} {r['values'][bit]}."}]
                 for i,(r,bit) in enumerate(zip(config["roles"],truth,strict=True))]
        phases=[game.EMPTY]+[tuple(step["public_after"]) for step in episode["steps"]]
        for index,state in enumerate(phases):
            grade_case={"id":f"{episode['id']}/{index}","track":"workshop","word_cap":225,
                        "gold":[game.terminal(menu,tuple(truth))[0]],"owned":private,
                        "task":"Record the two historical votes and the separate fictional workshop outcome. "
                               "Use the Decision line before the body and preserve the state of public evidence.",
                        "rubric":E.read(HERE/"rubric.json"),
                        "public":[*public,{"id":"delivered","text":public_conditions(config,state)}]}
            text=render(config,menu,state)
            calls=[{},{},{"text":text,"termination":"complete"}]
            assert len(text.split())<=grade_case["word_cap"]
            packet=E.final_packet(grade_case,calls)
            cases[grade_case["id"]] = grade_case,calls,packet
    return cases


def score(cases):
    marks=E.read(HERE/"marks.json")
    assert marks.keys()=={p["id"] for _,_,p in cases.values()}
    return {"written_states":len(cases),"scores":{
        phase:E.final_score(case,calls,marks[p["id"]]) for phase,(case,calls,p) in cases.items()
    }}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("verify","deck","score"))
    mode=parser.parse_args().mode
    if mode=="verify":
        E.emit(verify())
    else:
        cases=deck()
        E.emit([record[2] for record in cases.values()] if mode=="deck" else score(cases))
