"""Verify sequential collection and score the released witness records."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

import loop

HERE = Path(__file__).resolve().parent
RUN = HERE / "evidence"
E = loop.E
sys.path.insert(0, str(loop.plan.r.BENCH/"record-check"))
import replay as document


def read_rows(name):
    return [json.loads(line) for line in (RUN/name).read_text().splitlines()]


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def verify():
    from jinja2.sandbox import ImmutableSandboxedEnvironment
    from tokenizers import Tokenizer

    manifest = E.read(RUN/"complete.json")
    assert set(manifest) == {"launch.json","tokens.jsonl","episodes.jsonl","loop-lock.json"}
    assert all(digest(RUN/name)==value for name,value in manifest.items())
    assert E.read(RUN/"loop-lock.json")==loop.pins()
    launch=E.read(RUN/"launch.json")
    model=Path(launch["checkpoint"])
    assert digest(model/"model.safetensors.index.json")==launch["checkpoint_index_sha256"]
    assert launch["optimizer_updates"]==0
    assert launch["gpu_name"]=="NVIDIA RTX PRO 6000 Blackwell Server Edition"
    tokenizer=Tokenizer.from_file(str(model/"tokenizer.json"))
    template=ImmutableSandboxedEnvironment(trim_blocks=True,lstrip_blocks=True).from_string(
        (model/"chat_template.jinja").read_text())
    episodes=read_rows("episodes.jsonl")
    traces=iter(read_rows("tokens.jsonl"))
    recorded=iter([step for e in episodes for step in e["steps"]])
    eos=tokenizer.token_to_id("<|im_end|>")

    def supply(request):
        step=next(recorded)
        trace=next(traces)
        assert step["request"]==request and step["reply"]==trace["response"]
        text=template.render(messages=request["messages"],add_generation_prompt=True,
                             enable_thinking=False,tools=None)
        ids=tokenizer.encode(text,add_special_tokens=False).ids
        assert ids==trace["input_ids"] and len(ids)==step["reply"]["input_tokens"]
        out=trace["output_ids"]
        assert out and eos not in out[:-1]
        assert len(out)==step["reply"]["output_tokens"]<=request["max_output_tokens"]
        assert (out[-1]==eos)==(step["reply"]["termination"]=="complete")
        assert tokenizer.decode(out,skip_special_tokens=True).strip()==step["reply"]["text"]
        return step["reply"]

    replay=list(loop.execute(supply))
    assert next(traces,None) is None and next(recorded,None) is None
    assert json.loads(json.dumps(replay))==episodes
    return {"episodes":len(episodes),"verified_live_replies":sum(len(e["steps"]) for e in episodes),
            "optimizer_updates":0,"tokenizer_sha256":digest(model/"tokenizer.json")}


def packets():
    config,_,_,_ = loop.environment()
    worlds={w["id"]:w for w in config["worlds"]}
    deck, cases, outcomes = {}, {}, {}
    for row in read_rows("episodes.jsonl"):
        name=row["world"]
        case=document.case_inputs(config,worlds[name])
        pub={k:case[k] for k in ("roles","public","word_cap")}
        roles=dict(zip(loop.plan.ROLES,case["roles"],strict=True))
        paths=[("opening",row["opening"])]
        paths.extend((f"turn-{i}",loop.plan.get_log(tuple(step["state_after"])))
                     for i,step in enumerate(row["steps"],1))
        keymap={}
        for phase,log in paths:
            answer=document.render(pub,config["menu"],log)
            signs=" ".join(f"{roles[x['role']]} {'accepts' if x.get('accepts') else 'excludes'} "
                           f"{(x.get('accepts') or x['excludes'])[0]}." for x in log)
            judged=case | {"id":f"{case['id']}/{phase}","public":case["public"]+[
                {"id":"public-signs","text":signs or "No signs have been delivered."}]}
            calls=[{},{},{"text":answer,"termination":"complete"}]
            p=E.final_packet(judged,calls)
            deck[p["id"]]=p
            cases[p["id"]]=judged,calls
            keymap[phase]=p["id"]
        outcomes[name]={"ids":keymap,"accepted_replies":sum(s["admitted"] for s in row["steps"]),
                        "turns":len(row["steps"]),"decision":row["terminal"],
                        "proxy_gain":row["total_proxy_gain"],
                        "decisions_after_each_reply":[s["decision_after"] for s in row["steps"]]}
    return deck,cases,outcomes


def score(deck,cases,records):
    marks=E.read(HERE/"marks.json")
    assert set(marks)==set(deck)
    decisions={key:E.final_score(case,calls,marks[key]) for key,(case,calls) in cases.items()}
    for row in records.values():
        row["phases"]={phase:decisions[key] for phase,key in row["ids"].items()}
        row["released_gain"]=list(row["phases"].values())[-1]["released_70"]-row["phases"]["opening"]["released_70"]
        row["all_delivered_normalized_net"]=row["released_gain"]/70-row["turns"]*(loop.plan.ASK+loop.plan.SEND)
    return {"states_scored":len(deck),"live_paths":records,
            "annotation":"same-assistant exact-source review of deterministic compiled text"}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("verify","deck","score"))
    mode=parser.parse_args().mode
    if mode=="verify":
        output=verify()
    else:
        deck,cases,records=packets()
        output=[deck[k] for k in sorted(deck)] if mode=="deck" else score(deck,cases,records)
    E.emit(output)
