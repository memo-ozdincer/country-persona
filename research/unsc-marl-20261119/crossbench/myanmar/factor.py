"""Verify the remaining mandate fields separately and compose package proofs."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import runpy

HERE=Path(__file__).resolve().parent
base=runpy.run_path(str(HERE/"run.py"))
LOAD=base["load"]
LOCK=HERE/"factor-lock.json"
RAW=HERE/"evidence/predictions.jsonl"
FIELDS={
    "lead":{"restricted":"Only ASEAN-led consultation with United Nations support meets the requirement.",
            "either":"Both ASEAN-led consultation and joint ASEAN–United Nations chairing meet the requirement."},
    "safeguard":{"required":"An explicit confidentiality safeguard for individual case information is required.",
                 "optional":"The safeguard is optional. Either an explicit safeguard or no explicit safeguard meets this requirement."},
}
EXPECTED={"india":{"lead":"restricted","safeguard":"optional"},
          "uk-overlap":{"lead":"either","safeguard":"required"},
          "uk-impasse":{"lead":"either","safeguard":"required"}}


def suite():
    for role,card in LOAD(base["CASE"])["cards"].items():
        for field,choices in FIELDS.items():
            for index,values in enumerate((list(choices),list(reversed(choices)))):
                body={"private_mandate":card,"field":field,
                      "choices":dict(zip("AB",(choices[k] for k in values),strict=True))}
                yield {"id":f"{role}/{field}/{index}","labels":"AB","values":values,"messages":[
                    {"role":"system","content":"Read only the named field in this fictional mandate. Select the exact restriction, ignoring the publication schedule and all other fields. Respond with the answer letter."},
                    {"role":"user","content":json.dumps(body,ensure_ascii=False)},
                ]}


def score(rows):
    counts,fields=Counter(),{}
    examples={item["id"]:item for item in suite()}
    reader=LOAD(HERE/"evidence/metrics.json")
    original={r["id"]:r for r in map(json.loads,RAW.read_text().splitlines())}
    for role in EXPECTED:
        fields[role]={}
        for field,want in EXPECTED[role].items():
            orders=[]
            for i in range(2):
                key=f"{role}/{field}/{i}"
                logits=rows[key]["label_logits"]
                top=max(logits)
                best=[k for k,s in zip(examples[key]["values"],logits,strict=True) if s==top]
                orders.append(best[0] if len(best)==1 else None)
            stable=orders[0] if orders[0]==orders[1] else None
            status="unknown" if stable is None else "correct" if stable==want else "wrong"
            counts["field",status]+=1
            fields[role][field]={"value":stable,"answer_orders":orders,"reference":want}
    projects={}
    for role in EXPECTED:
        projects[role]={}
        group=reader["scope"][role]["winner"]
        for opt in LOAD(base["CASE"])["options"]:
            lead=fields[role]["lead"]["value"]
            guard=fields[role]["safeguard"]["value"]
            satisfied=(
                None if group is None else opt["scope"] not in base["GROUPS"][group],
                None if lead is None else lead=="either" or opt["lead"]=="asean",
                None if guard is None else guard=="optional" or opt["safeguard"],
            )
            value=False if False in satisfied else None if None in satisfied else True
            projects[role][opt["id"]]={"projected_sign":value,"field_pass":satisfied}
    composed={}
    for expected in base["suite"]():
        id_=expected["id"]
        role,kind,option,_=id_.split("/")
        if kind=="scope":
            composed[id_]=original[id_]
            continue
        sign=projects[role][option]["projected_sign"]
        code=None if sign is None else "accept" if sign else "reject"
        composed[id_]={"label_logits":[float(x==code) for x in expected["values"]]}
    replay=base["score"](composed)
    return {"totals":{**replay["totals"],**{"/".join(k):v for k,v in counts.items()}},
            "fields":fields,"projection_basis":projects,"scope":replay["scope"],
            "package":replay["package"],"paths":replay["paths"],
            "scope_note":"Package signs are a deterministic projection from three role-local fields. They are carried into the existing scorer via synthetic scores, not new package logits."}


def digests():
    root=HERE.parents[1]
    paths=(Path(__file__),HERE/"run.py",HERE/"case.json",RAW,RAW.parent/"metrics.json",
           base["TRAINED"],base["scope_sets"].ENTAILMENT/"field_panel.py")
    return {str(p.resolve().relative_to(root)):sha256(p.read_bytes()).hexdigest() for p in paths}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("lock","run","replay"))
    p.add_argument("output",type=Path,nargs="?")
    p.add_argument("--model",type=Path)
    args=p.parse_args()
    if args.mode=="lock":
        assert len(list(suite()))==12
        with LOCK.open("x") as f:
            json.dump({"calls":12,"hashes":digests(),"scope":"Same case. Read remaining non-scope conditions independently; compose them with the archived scope read."},f,indent=2)
            f.write("\n")
        return
    assert LOAD(LOCK)["hashes"]==digests()
    if args.mode=="run":
        panel=base["scope_sets"].field_panel
        panel.suite,panel.score=suite,score
        panel.main(args.model,args.output)
        return
    path=args.output/"predictions.jsonl"
    assert LOAD(args.output/"complete.json")=={"records":12,"sha256":sha256(path.read_bytes()).hexdigest()}
    records=list(map(json.loads,path.read_text().splitlines()))
    for plan,row in zip(suite(),records,strict=True):
        assert all(row[k]==v for k,v in plan.items())
    result=score({r["id"]:r for r in records})
    assert json.loads(json.dumps(result))==LOAD(args.output/"metrics.json")
    print(json.dumps({"calls":len(records),"hashes":len(digests()),"paths":len(result["paths"]),"exact":True}))


if __name__=="__main__":
    main()
