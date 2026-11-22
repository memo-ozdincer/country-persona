"""Audit package and scope evidence independently, before any authored guard."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
SPACE=HERE.parent
MALI=HERE.parents[1]/"mali"
MENUS={"japan":"ADF","china-overlap":"BFG","china-impasse":"BG",
       "france-overlap":"AEG","france-impasse":"AG","russia":"CE"}


def load(path):
    return json.loads(path.read_text())


def audit():
    sources={"space_case":SPACE/"case.json","space_signs":SPACE/"evidence/metrics.json",
             "mali_case":MALI/"case.json","mali_signs":MALI/"evidence/metrics.json",
             **{k:SPACE/f"evidence/{k}/metrics.json" for k in ("scope-model","scope-questions","scope-sets")}}
    data={k:load(v) for k,v in sources.items()}
    menus,totals={},Counter()
    for family in ("space","mali"):
        case=data[f"{family}_case"]
        raw=data[f"{family}_signs"]
        methods={"mali-whole":raw["published_scope_candidates"]["whole_set"]} if family=="mali" else {
            "space-direct-scope":data["scope-model"]["published_scope_candidates"],
            **{f"{name}/{wording}":{
                role:data[name]["projections"][f"{wording}/{role}"]["rejected_scopes"]
                for role in case["cards"]} for name in ("scope-questions","scope-sets")
               for wording in ("original","reworded")}
        }
        for role in case["cards"]:
            options=[p["id"] for p in case["options"]]
            signs={k:(raw["package_predictions"][role][k]["sign"] if family=="mali"
                      else raw["decisions"][f"{role}/{k}"]["sign"]) for k in options}
            yes={k for k,v in signs.items() if v is True}
            no={k for k,v in signs.items() if v is False}
            unresolved=set(options)-yes-no
            for name,domain in methods.items():
                derived={p["id"] for p in case["options"] if p["scope"] in domain[role]}
                conflict=derived&yes
                newly_known=derived&unresolved
                # The whole conflicting proof stays unavailable. Do not reinterpret the
                # disputed positive or negative with the hidden workshop menu.
                final_yes=yes-conflict
                usable_scope=derived if not conflict else set()
                final_no=no|usable_scope
                combined={k:True if k in final_yes else False if k in final_no else None for k in options}
                gold=set(MENUS[role])
                for method,score in (("package",signs),("separate",combined)):
                    totals[name,method,"available"]+=sum(v is not None for v in score.values())
                    totals[name,method,"wrong"]+=sum(v is not None and v!=(k in gold) for k,v in score.items())
                totals[name,"scope_conflicts"]+=len(conflict)
                totals[name,"new_verified_exclusions"]+=len(usable_scope&unresolved)
                menus[f"{name}/{role}"]={
                    "direct":signs,"active_scope_exclusions":sorted(usable_scope),
                    "raw_scope_exclusions":sorted(derived),"positive_scope_conflicts":sorted(conflict),
                    "raw_new_negatives":sorted(newly_known),"admissible_new_negatives":sorted(usable_scope&unresolved),
                    "admissible_signs":combined,
                }
    return {"scope":"Archived, order-stable model decisions. The direct/package read and scope read never substitute for each other. Hidden menu used only for scoring.",
            "inputs":{k:sha256(path.read_bytes()).hexdigest() for k,path in sources.items()},
            "totals":{"/".join(k):v for k,v in totals.items()},"sources_by_role":menus}


if __name__=="__main__":
    print(json.dumps(audit(),indent=2))
