"""Two-docket factorial comparison using the project's frozen CPU writer."""
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
KIT = HERE.parent
sys.path.insert(0,str(KIT.parent/"validity-audit"))
import source_record_run as runner

DATA = KIT/"facilitator-new-meetings.json"
PROTOCOL = HERE/"protocol.json"
ARMS = ("independent","peer","solo")


def request(key,cap,instruction,payload):
    return {"id":key,"cap":cap,"messages":[{"role":"system","content":instruction},
            {"role":"user","content":json.dumps(payload,ensure_ascii=False)}]}


def episode(generate):
    cases=json.loads(DATA.read_text())
    protocol=json.loads(PROTOCOL.read_text())
    rows={}
    def read(requests):
        rows.update(generate(requests))
    for name,data in cases.items():
        # Both independent local notes are reused whenever their information is identical.
        desks=data["sources"]
        read([request(f"{name}/local/{j}",76,protocol["note_task"],
                      {"assigned":speaker,"source":card}) for j,(speaker,card) in enumerate(desks)])
        read([request(f"{name}/solo-first/{j}",76,protocol["note_task"],
                      {"assigned":speaker,"sources":desks}) for j,(speaker,_) in enumerate(desks)])
        second=[]
        for j in (0,1):
            k=1-j
            for arm in ("peer","solo"):
                key=f"{name}/"+("local" if arm=="peer" else "solo-first")+f"/{j}"
                payload={"assigned":desks[k][0],"earlier_note":rows[key]["output"]}
                payload.update({"source":desks[k][1]} if arm=="peer" else {"sources":desks})
                second.append(request(f"{name}/{arm}-second/{j}",76,protocol["note_task"],payload))
        read(second)
        finals=[]
        for j in (0,1):
            for arm in ARMS:
                keys=trace(name,arm,j)
                notes=[{"desk":desks[s][0],"note":rows[key]["output"]} for s,key in zip((j,1-j),keys[:2])]
                finals.append(request(keys[-1],150,protocol["task"],{"desk_notes":notes}))
        read(finals)
    return [{"family":"chair-brief-crossover","final":rows}]


def trace(name,arm,j):
    first="solo-first" if arm=="solo" else "local"
    second=f"local/{1-j}" if arm=="independent" else f"{arm}-second/{j}"
    return [f"{name}/{first}/{j}",f"{name}/{second}",f"{name}/{arm}/final/{j}"]


def pins():
    return {p.name:runner.digest(p) for p in [DATA,PROTOCOL,Path(__file__),Path(runner.__file__)]}


if __name__=="__main__":
    model=Path("/mfs1/u/memo/country-persona-research/models/Qwen3.5-4B/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a")
    with patch.multiple(runner,episode=episode,locks=pins):
        runner.run(model,HERE/"evidence")
