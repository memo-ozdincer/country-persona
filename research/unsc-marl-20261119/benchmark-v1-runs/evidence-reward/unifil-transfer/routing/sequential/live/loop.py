"""Run the frozen UNIFIL two-question planner with actual sequential Qwen replies."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SEQ = HERE.parent
RUNS = SEQ.parents[3]
sys.path.insert(0, str(SEQ))
import sequential as plan
sys.path.insert(0, str(RUNS / "syria-baseline"))
import collect as base

E = plan.E
SYSTEM = (
    "You are the named delegate in a fictional briefing workshop. Answer whether the queried briefing "
    "satisfies your own requirement using your private note and the option description. Prior public signs "
    "are context and cannot change your private requirement. Return exactly Y if the queried option meets "
    "your requirement or N if it does not. Send the sign even if it does not settle the workshop. No prose."
)
NOTES = {
    ("cadence", "weekly"): "The briefing has to be held every week. I can accept either presentation format.",
    ("cadence", "monthly"): "I can accept the briefing only if it is held once a month. The format is flexible.",
    ("format", "written"): "The briefing must be delivered in writing. All listed briefing frequencies are acceptable.",
    ("format", "oral"): "I can accept a spoken briefing at any of the listed frequencies. It has to be oral.",
}


def environment():
    bench = plan.r.BENCH
    public = E.read(bench/"case.json")
    tree = E.read(bench/"transfer-fit.json")["tree"]
    display, choose, _ = plan.fixture(public["menu"],tree,.80)
    witnesses = E.read(SEQ/"sequential.json")["results"]["0.8"]["bridge_witnesses"]
    return public, display, choose, witnesses


def state_of(log):
    result=[0]*len(plan.QUERIES)
    for row in log:
        result[int(row["id"])]=1 if row.get("accepts") else -1
    return tuple(result)


def request(public, world, state, query):
    names = dict(zip(plan.ROLES, public["roles"], strict=True))
    role, option = plan.QUERIES[query]
    private = world["requirements"][plan.ROLES.index(role)]
    typed, = private.items()
    chosen = next(p for p in public["menu"] if p["id"] == option)
    log = [{**row,"role":names[row["role"]]} for row in plan.get_log(state)]
    content = {"delegate":names[role],"own_workshop_note":NOTES[typed],
               "query":f"Does briefing option {option} satisfy your own requirement?",
               "option":f"{chosen['cadence']} {chosen['format']} briefing",
               "previous_public_signs":log}
    return {"max_output_tokens":32,"messages":[{"role":"system","content":SYSTEM},
                                               {"role":"user","content":json.dumps(content,ensure_ascii=False)}]}


def execute(generate):
    public, display, choose, witnesses = environment()
    worlds = {world["id"]:world for world in public["worlds"]}
    for key, example in witnesses.items():
        world = worlds[key]
        opening = state_of(example["opening"])
        state = opening
        trace=[]
        for left in (2,1):
            query,_ = choose(state,left,"learned")
            if query is None:
                break
            outgoing=request(public,world,state,query)
            reply=generate(outgoing)
            role, option = plan.QUERIES[query]
            truth = option in plan.r.a.accepted(public["menu"],world["requirements"][plan.ROLES.index(role)])
            sign = {"Y":True,"N":False}.get(reply["text"]) if reply["termination"]=="complete" else None
            admitted = sign is not None and sign==truth
            after = plan.advance(state,query,sign) if admitted else state
            trace.append({"state_before":state,"query":[role,option],"request":outgoing,"reply":reply,
                          "admitted":admitted,"truth":"Y" if truth else "N","state_after":after,
                          "decision_before":display(state)[0],"decision_after":display(after)[0],
                          "proxy_gain":display(after)[1]-display(state)[1]})
            state=after
        yield {"world":key,"opening":plan.get_log(opening),"steps":trace,"final_log":plan.get_log(state),
               "terminal":display(state)[0],"total_proxy_gain":display(state)[1]-display(opening)[1]}


def pins():
    paths = (Path(__file__),HERE/"protocol.md",SEQ/"sequential.json",SEQ/"sequential.py",
             plan.r.BENCH/"case.json",plan.r.BENCH/"transfer-fit.json")
    return {str(p.relative_to(RUNS)):sha256(p.read_bytes()).hexdigest() for p in paths}


def collect(generate, directory):
    for row in execute(generate):
        base.suite.append(directory/"episodes.jsonl",row)
    (directory/"loop-lock.json").write_text(json.dumps(pins(),indent=2)+"\n")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("deck","run"))
    if parser.parse_args().mode=="deck":
        public,_,choose,witnesses=environment()
        worlds={world["id"]:world for world in public["worlds"]}
        out={}
        for key,row in witnesses.items():
            initial=state_of(row["opening"])
            query,_=choose(initial,2,"learned")
            assert plan.QUERIES[query]==tuple(row["first_query"])
            out[key]=request(public,worlds[key],initial,query)
        E.emit(out)
    else:
        _,_,_,witnesses=environment()
        with patch.object(base.suite,"collect",collect),patch.object(base,"roster",return_value=witnesses):
            base.run(HERE/"evidence")
