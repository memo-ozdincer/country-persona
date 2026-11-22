"""Skip retries that cannot improve the documented score from an empty receipt."""
from itertools import product
from pathlib import Path
from statistics import mean

import torch

import retry as r

HERE = r.HERE


def guard(scene,p,q):
    # With no remaining packets delivered, the retry can reach only a public singleton.
    remove = torch.as_tensor(scene["bank"][1:3] <= scene["bank"][0])
    p, q = p.clone(), q.clone()
    q[0,:,0] += q[0,:,1:][:,remove].sum(-1)
    q[0,:,1:][:,remove] = 0
    if bool(remove.all()):
        p[0] = 0
    return p,q


def evaluate(rows, weights, accuracy, old):
    records = []
    sources = r.corpus(rows,accuracy)
    for (family,name,law,scene), earlier in zip(sources,old,strict=True):
        p,q = r.strategy(scene,weights,True)
        p,q = guard(scene,p,q)
        nets = tuple(float(v) for v in r.expected(scene,p,q))
        check = r.independent_check(scene,p,q)
        assert all(abs(a-b)<1e-8 for a,b in zip(nets,check,strict=True))
        previous = earlier["outcomes"]["learned_greedy"]
        assert nets[0] >= previous["net"] - 1e-10
        assert nets[1] >= previous["release"] - 1e-10
        assert nets[2] <= previous["retries"] + 1e-10
        records.append({"family":family,"bank":name,"law":law,"scores":scene["bank"].tolist(),
                        "net":nets[0],"release":nets[1],"retries":nets[2],"hints":nets[3],
                        "delta_net":nets[0]-previous["net"],"delta_release":nets[1]-previous["release"]})
    return records


def run():
    torch.set_num_threads(1)
    archive,held = r.point_banks()
    old = r.read(HERE/"results.json")["groups"]
    result = {}
    for name, fitting in old.items():
        source = held if name=="transfer" else [row for row in archive if row[0]==name]
        weights = [torch.tensor(w,dtype=r.D) for w in fitting["weights"]]
        result[name] = {}
        for tag, p in (("matched",.85),("stressed",.65)):
            records = evaluate(source,weights,p,fitting["test"][tag]["rows"])
            means = {key:mean(row[key] for row in records) for key in
                     ("net","release","retries","hints","delta_net","delta_release")}
            result[name][tag] = {"means":means,"rows":records,
                                 "conditions_improved":sum(row["delta_net"]>1e-9 for row in records)}
    overall = {tag:{key:mean(groups[tag]["means"][key] for name,groups in result.items() if name!="transfer")
                    for key in ("net","delta_net","delta_release")}
               for tag in ("matched","stressed")}
    pins = (Path(__file__),HERE/"results.json",HERE/"comparison.json")
    return {"scope":"Post hoc public-action dominance guard over the frozen greedy policy.",
            "archive_macro":overall,"groups":result,"sha256":{p.name:r.digest(p) for p in pins}}


if __name__ == "__main__":
    print(r.json.dumps(run(),indent=2))
