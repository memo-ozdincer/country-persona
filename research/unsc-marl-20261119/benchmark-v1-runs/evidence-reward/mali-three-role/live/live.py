"""Execute a three-role fitted chair against sequential native Qwen replies."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
BENCH=HERE.parent
RUNS=BENCH.parents[1]
sys.path.insert(0,str(BENCH))
import experiment as game
sys.path.insert(0,str(RUNS/"syria-baseline"))
import collect as base

E=base.suite.e
DELIVERY=(.9,.9,.9)
BUDGET={"agreement":3,"early-impasse":2}
SYSTEM=(
    "You are the named participant in a fictional post-meeting workshop. The question asks whether package A "
    "meets your own one-field requirement. Read only your own private requirement and the matching package term. "
    "Prior disclosed requirements refer to other questions and cannot change your own requirement. "
    "Respond Y if package A meets your requirement and N if it does not. Return one letter only."
)


def design():
    case=game.read(BENCH/"case.json")
    menu=tuple(tuple(option) for option in case["packages"].values())
    tree=game.read(BENCH/"experiment.json")["learned_tree"]
    exact,_=game.solver(menu,DELIVERY)

    def choose(state,left):
        return game.select("learned",state,left,menu,DELIVERY,exact,tree)

    picked={}
    for label,budget in BUDGET.items():
        for world in game.WORLDS:
            state=game.EMPTY
            turns=[]
            for left in range(budget,0,-1):
                role=choose(state,left)
                if role is None:
                    break
                turns.append(role)
                state=game.write_bit(state,role,world[role])
            decision=game.terminal(menu,state)[0]
            valid = decision not in ("A","IMPASSE","UNRESOLVED") if label=="agreement" else decision=="IMPASSE"
            if valid and len(turns)==budget:
                picked[label]=world
                break
    assert set(picked)=={"agreement","early-impasse"}
    return case,menu,choose,picked


def request(case,role,bit,state):
    card=case["roles"][role]
    prior={r["name"]:r["values"][known] for r,known in zip(case["roles"],state,strict=True) if known>=0}
    content={"role":card["name"],"simulated_requirement":f"The {card['field']} must be {card['values'][bit]}.",
             "package_a_term":f"The {card['field']} is {card['values'][case['packages']['A'][role]]}.",
             "public_disclosed_requirements":prior}
    return {"max_output_tokens":32,"messages":[{"role":"system","content":SYSTEM},
                                               {"role":"user","content":json.dumps(content,ensure_ascii=False)}]}


def execute(generate):
    case,menu,choose,picked=design()
    for key,truth in picked.items():
        state=game.EMPTY
        trace=[]
        for left in range(BUDGET[key],0,-1):
            role=choose(state,left)
            if role is None:
                break
            req=request(case,role,truth[role],state)
            reply=generate(req)
            sign={"Y":True,"N":False}.get(reply["text"]) if reply["termination"]=="complete" else None
            expected=truth[role]==case["packages"]["A"][role]
            admitted=sign is not None and sign==expected
            value=case["packages"]["A"][role] if sign else 1-case["packages"]["A"][role]
            after=game.write_bit(state,role,value) if admitted else state
            trace.append({"role":role,"public_before":state,"request":req,"reply":reply,
                          "admitted":admitted,"public_after":after,"decision":game.terminal(menu,after)[0]})
            state=after
        result=game.terminal(menu,state)
        answer=game.terminal(menu,truth)[0]
        assert result[0] in (answer,"UNRESOLVED")
        yield {"id":key,"evaluator_world":truth,"steps":trace,"decision":result[0],"proxy":result[1]}


def pins():
    files=(Path(__file__),HERE/"protocol.md",HERE/"opening-requests.json",BENCH/"case.json",BENCH/"experiment.json",
           BENCH/"experiment.py")
    return {str(p.relative_to(RUNS)):sha256(p.read_bytes()).hexdigest() for p in files}


def opening_requests():
    case,_,choose,picked=design()
    result={}
    for name,truth in picked.items():
        role=choose(game.EMPTY,BUDGET[name])
        result[name]=request(case,role,truth[role],game.EMPTY)
    return result


def collect(generate,path):
    assert opening_requests()==E.read(HERE/"opening-requests.json")
    for item in execute(generate):
        base.suite.append(path/"episodes.jsonl",item)
    (path/"loop-lock.json").write_text(json.dumps(pins(),indent=2)+"\n")


if __name__=="__main__":
    parse=argparse.ArgumentParser(description=__doc__)
    parse.add_argument("mode",choices=("deck","run"))
    if parse.parse_args().mode=="deck":
        E.emit(opening_requests())
    else:
        with patch.object(base.suite,"collect",collect),patch.object(base,"roster",return_value=design()[3]):
            base.run(HERE/"evidence")
