"""Train new local policies from source-scoped rewards on additional dockets."""
from importlib.util import module_from_spec, spec_from_file_location
from itertools import product
import json
import sys
from unittest.mock import patch

import numpy as np

from collect_transfer_dockets import HERE, RUNS, TRAIN, serial, read

# Load the old learner with its own sibling imports before restoring the path.
def load_value():
    sys.path.insert(0, str(TRAIN))
    try:
        spec = spec_from_file_location("transfer_value_learner", TRAIN / "value_sender.py")
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


learner = load_value()
team = learner.team


def margin(outputs, key):
    ab, ba = (outputs[f"{key}/{order}"]["logits"] for order in ("ab", "ba"))
    return (ab["A"]-ab["B"]+ba["B"]-ba["A"])/2


def bank(cases, outputs):
    public, first, last, both, obs = (np.zeros(shape, dtype=int)
        for shape in ((2,), (2,3), (2,2), (2,3,2), (2,3)))
    authored, reviewed = both.copy(), both.copy()
    records = {}
    for i,(d,case) in enumerate(cases.items()):
        weights = {r["id"]:r["weight"] for r in case["rubric"]}
        public[i] = sum(weights[id_] for id_ in case["public"])
        for v,(early,a) in enumerate(case["early"].items()):
            x = margin(outputs, f"{d}/early/{early}")
            obs[i,v] = 1+int(x>0)
            first[i,v] = public[i] + sum(weights.get(id_,0) for id_ in a["record"])
            for r,(late,b) in enumerate(case["late"].items()):
                y = margin(outputs, f"{d}/late/{late}")
                last[i,r] = public[i] + sum(weights.get(id_,0) for id_ in b["record"])
                approved = x>0 and y>0
                actual = early=="full" and late=="relational"
                pieces = [*case["public"].values(), *a["record"].values(), *b["record"].values()]
                prose = " ".join([*pieces,*([case["clause"]] if approved else [])])
                assert len(prose.split())<=case["cap"], (d,early,late,len(prose.split()))
                base = first[i,v] + last[i,r] - public[i]
                bonus = weights[case["relation"]]
                both[i,v,r] = base + bonus*approved
                reviewed[i,v,r] = both[i,v,r] if not approved or actual else 0
                authored[i,v,r] = base + bonus*actual
                records[f"{d}/{early}/{late}"] = {"answer":prose,"margins":[x,y],"native_accepts":approved,
                    "key_accepts":actual,"training_score":int(both[i,v,r]),"audited_score":int(reviewed[i,v,r]),
                    "authored_score":int(authored[i,v,r])}
    return (public,first,last,both,obs),(public,first,last,reviewed,obs),authored,records


def run():
    spec = serial()
    assert spec==read(HERE/"plan.json")
    outputs=read(HERE/"verified.json")["outputs"]
    assert set(outputs)=={r["id"] for r in spec["requests"]}
    cases = spec["cases"]
    trained,audited,authored,records=bank(cases,outputs)
    with patch.object(team,"PRIVATE",{k:tuple(v["early"]) for k,v in cases.items()}):
        v=learner.train(trained)
        with patch.object(team,"BATCH",2*team.BATCH):
            pg=team.train(trained)
        out=learner.fit.compare(audited,v[:2],pg[:2])
        misses=learner.send_audit(audited,out["held"])
    return {"records":records, "native_and_authored_tables_match": bool(np.array_equal(trained[3],authored)),
            "comparison":out,"value_history":v[2],"sampled_history":pg[2],
            "learned_sender_mismatches":misses}


if __name__=="__main__":
    print(json.dumps(run(),ensure_ascii=False,indent=2))
