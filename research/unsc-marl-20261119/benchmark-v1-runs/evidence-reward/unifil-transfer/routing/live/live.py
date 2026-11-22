"""Collect four localized live replies to the learned UNIFIL router's selected questions."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROUTING = HERE.parent
BENCH = ROUTING.parent
RUNS = BENCH.parents[1]
sys.path.insert(0, str(ROUTING))
import route
sys.path.insert(0, str(RUNS / "syria-baseline"))
import collect as base

E = route.E
SYSTEM = (
    "You are the named participant in a fictional procedural workshop. The chair asks whether a single "
    "proposed briefing fits your private requirement. Use only your own note and the option description. "
    "Return one letter, Y if the option satisfies your requirement, or N if it does not. No prose."
)
LOCAL_TEXT = {
    ("cadence","weekly"): "For this workshop, I can accept a briefing that takes place every week. Either presentation format works.",
    ("cadence","monthly"): "I can agree to the workshop plan only if the briefing is held once a month. The presentation format is open.",
    ("format","written"): "Either of the available dates works for the fictional exercise, but the briefing has to come in writing.",
    ("format","oral"): "The fictional workshop briefing has to be spoken. Its frequency can be any of the listed cadences.",
}


def cases():
    config = E.read(BENCH/"case.json")
    worlds = {w["id"]:w for w in config["worlds"]}
    results = {}
    diff = E.read(ROUTING/"route.json")["results"]["0.8"]["query_differences"]
    assert len(diff) == 2
    for i, row in enumerate(diff):
        assert row["arms"]["exact_record"]["question"] is None
        results[f"waste-{i+1}"] = (worlds[row["world"]], row["signs"], row["arms"]["learned_team"])

    controls = {}
    tree = E.read(BENCH/"transfer-fit.json")["tree"]
    for world in config["worlds"]:
        menu = config["menu"]
        own = [route.a.accepted(menu,r) for r in world["requirements"]]
        claims = [route.a.public.signed.claim(f"{i}/{opt}",role,opt in own[i],opt)
                  for i,role in enumerate(route.ROLES) for opt in route.OPTIONS]
        for opening in route.a.subsets(claims):
            log = list(opening)
            old, values = route.context(menu,log,tree)
            first, v = route.choice(values,.8,"learned")
            second, _ = route.choice(values,.8,"record")
            if first is None or first != second or old != "UNRESOLVED":
                continue
            branch = route.outcome(first,v,values,.8,own,"learned")
            if branch["proof_gain"] > 0.:
                controls.setdefault(branch["truthful_reply"],(world,log,branch))
    assert set(controls) == {False,True}
    results["productive-yes"] = controls[True]
    results["productive-no"] = controls[False]
    return config, results


def deck():
    config, rows = cases()
    descriptions = {row["id"]: f"{row['cadence']} {row['format']} briefing" for row in config["menu"]}
    out = []
    for key,(world,_,route_row) in rows.items():
        role, option = route_row["question"]
        idx = route.ROLES.index(role)
        typed, = world["requirements"][idx].items()
        payload = {"role": config["roles"][idx], "private_note":LOCAL_TEXT[typed],
                   "question": f"Does package {option} satisfy your local requirement?",
                   "queried_option": descriptions[option]}
        out.append({"id":key,"request":{"max_output_tokens":32,"messages":[
            {"role":"system","content":SYSTEM},{"role":"user","content":json.dumps(payload,ensure_ascii=False)}
        ]}})
    return out


def pins():
    files=(Path(__file__),HERE/"protocol.md",HERE/"requests.json",BENCH/"case.json",ROUTING/"route.json")
    return {str(p.relative_to(RUNS)):sha256(p.read_bytes()).hexdigest() for p in files}


def collect(generate,path):
    expected=E.read(HERE/"requests.json")
    assert expected==deck()
    for row in expected:
        base.suite.append(path/"records.jsonl",{**row,"response":generate(row["request"])})
    (path/"route-lock.json").write_text(json.dumps(pins(),indent=2)+"\n")


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("deck","run"))
    if p.parse_args().mode=="deck":
        E.emit(deck())
    else:
        roster={r["id"]:r for r in deck()}
        with patch.object(base.suite,"collect",collect), patch.object(base,"roster",return_value=roster):
            base.run(HERE/"evidence")
