"""Find certificates supported by the available receipts under the source limit."""
import argparse
from itertools import product
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def evaluate(metrics):
    metrics=metrics.get("replay",metrics)
    case=json.loads((HERE/"case.json").read_text())
    options={p["id"] for p in case["options"]}
    results={}
    for role in ("uk-overlap","uk-impasse"):
        sides=("india",role)
        inventory={}
        for card in sides:
            current,late,scope=[set(),set()],[set(),set()],set(metrics["scope"][card]["admitted_exclusions"])
            for opt,data in metrics["package"][card].items():
                value=data["admitted"]
                if value is None:
                    continue
                destination=late if opt in case["later_only"][card] else current
                destination[0 if value else 1].add(opt)
            inventory[card]={"initial":current,"later":late,"scope":scope}
        experiments=[]
        for side in sides:
            fields=inventory[side]
            ops=[("none",set(),set()),("scope",set(),fields["scope"])]
            for sign,labels in enumerate(fields["later"]):
                ops.extend(("package", {label} if sign==0 else set(), {label} if sign==1 else set())
                           for label in sorted(labels))
            experiments.append(ops)
        solutions=[]
        for a,b in product(*experiments):
            if a[0]==b[0]=="package":
                continue
            yes=[inventory[side]["initial"][0]|move[1] for side,move in zip(sides,(a,b),strict=True)]
            no=[inventory[side]["initial"][1]|move[2] for side,move in zip(sides,(a,b),strict=True)]
            state="AGREEMENT_POSSIBLE" if yes[0]&yes[1] else "IMPASSE" if no[0]|no[1]==options else "UNRESOLVED"
            if state!="UNRESOLVED":
                solutions.append({"state":state,"sources":[a[0],b[0]],
                                  "overlap":sorted(yes[0]&yes[1]),"excluded":sorted(no[0]|no[1])})
        results[role]={
            "initial_and_late":{k:{"initial":[sorted(x) for x in v["initial"]],
                                   "later":[sorted(x) for x in v["later"]],"scope_excludes":sorted(v["scope"])}
                                for k,v in inventory.items()},
            "full_information_possible_proofs":solutions,
        }
    return {"scope":"Clairvoyant availability bound. It assumes all supported signs can be published within turns. At most one source per role and at most one late package answer total.",
            "cases":results}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("metrics",type=Path)
    print(json.dumps(evaluate(json.loads(p.parse_args().metrics.read_text())),indent=2))
