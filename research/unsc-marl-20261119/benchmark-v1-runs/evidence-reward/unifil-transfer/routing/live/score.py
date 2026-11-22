"""Score live reply truth and compile both public records with the held rubric."""
import argparse
import json
from pathlib import Path
import sys

import live

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(live.BENCH/"record-check"))
import replay as document

E, route = live.E, live.route


def records():
    actual = E.judge.by_id([json.loads(l) for l in (HERE/"evidence/records.jsonl").read_text().splitlines()])
    config, selections = live.cases()
    assert set(actual) == set(selections)
    for key,(world,opening,selected) in selections.items():
        role,option=selected["question"]
        reply=actual[key]["response"]
        raw=reply["text"]
        proposed={"Y":True,"N":False}.get(raw) if reply["termination"]=="complete" else None
        admitted=proposed is not None and proposed==selected["truthful_reply"]
        updated=opening + [route.a.public.signed.claim("reply",role,proposed,option)] if admitted else opening
        data={"reply":reply,"admitted":admitted,"query":selected["question"],
              "expected_sign":"Y" if selected["truthful_reply"] else "N",
              "tree_predicted_net":selected["projected"]}
        yield key,config,world,opening,updated,data


def prepare():
    cases={}
    packets={}
    mapping={}
    for key,config,world,opening,updated,data in records():
        context=document.case_inputs(config,world)
        public={k:context[k] for k in ("roles","public","word_cap")}
        data["phases"]={}
        names=dict(zip(route.ROLES,context["roles"],strict=True))
        for phase,log in (("before",opening),("after",updated)):
            answer=document.render(public,config["menu"],log)
            if phase=="after" and log==opening:
                data["phases"]["after"]=data["phases"]["before"]
                continue
            scoped=" ".join(f"{names[claim['role']]} {'accepts' if claim.get('accepts') else 'excludes'} "
                            f"{(claim.get('accepts') or claim['excludes'])[0]}." for claim in log)
            case=context | {"id":f"{context['id']}/{key}/{phase}","public":[*context["public"],
                                  {"id":"public-signs","text":scoped or "No signs have been delivered."}]}
            calls=[{},{},{"text":answer,"termination":"complete"}]
            packet=E.final_packet(case,calls)
            identifier=packet["id"]
            cases[identifier]=case,calls
            packets[identifier]=packet
            data["phases"][phase]=identifier
        mapping[key]=data
    return cases,packets,mapping


def score(cases,packets,mapping):
    marks=E.read(HERE/"marks.json")
    assert marks.keys()==packets.keys()
    grades={key:E.final_score(case,calls,marks[key]) for key,(case,calls) in cases.items()}
    outcomes={}
    for key,item in mapping.items():
        judged={phase:grades[pid] for phase,pid in item["phases"].items()}
        gain=judged["after"]["released_70"]-judged["before"]["released_70"]
        net=.8*gain/70-route.ASK-route.SEND
        outcomes[key]={**item,"grades":judged,"released_gain_if_delivered":gain,
                       "expected_net_at_0.8":net}
    return {"cases":len(outcomes),"admitted":sum(row["admitted"] for row in outcomes.values()),"records":outcomes}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("deck","score"))
    cases,packets,mapping=prepare()
    E.emit([packets[x] for x in sorted(packets)] if parser.parse_args().mode=="deck"
           else score(cases,packets,mapping))
