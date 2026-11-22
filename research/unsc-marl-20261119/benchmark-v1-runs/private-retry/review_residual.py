"""Learn a fee-aware review override and count informative reviews."""
from collections import Counter
from itertools import product
from pathlib import Path
from statistics import mean

import numpy as np
import torch

import review as original

r, HERE = original.r, original.HERE
COSTS = original.FEES


def features(scene,mask,fee):
    head = original.view(scene,mask,fee)
    visible = scene["bank"][:3]
    return np.r_[head, float(min(visible[1:])==0), float(min(visible[1:])<=visible[0])]


def branch(scene,mask,fee):
    values,_,approved = original.effects(scene,mask,fee)
    base = int(original.choose(scene,mask,fee,"fixed:+7",None).argmax())
    assert base in (0,1)
    affected = bool(base!=approved)
    return values[2]-values[base], affected, base, approved


def fit(rows):
    cases = r.corpus(rows,.85)
    count = Counter(t[0] for t in cases)
    examples = [(features(scene,mask,fee), branch(scene,mask,fee)[0]/(len(count)*count[family]*len(COSTS)))
                for family,_,_,scene in cases for mask,fee in product((1,2),COSTS)]
    x,y = np.stack([a for a,_ in examples]), np.asarray([b for _,b in examples])
    w=np.zeros(x.shape[1])
    def objective(w):
        p=1/(1+np.exp(-x@w))
        return float(p@y), x.T@(p*(1-p)*y)-r.PENALTY*w
    begin,g = objective(w)
    for j,axis in enumerate(np.eye(len(w))*1e-5):
        assert abs((objective(w+axis)[0]-objective(w-axis)[0])/2e-5-g[j]) < 1e-8
    for _ in range(r.STEPS):
        _,g=objective(w)
        w+=r.STEP*g
    end,_=objective(w)
    assert end>=begin
    return w,[begin,end]


def evaluate(source, baseline, weights):
    overall={}
    for tag,acc in (("matched",.85),("stressed",.65)):
        overall[tag]={}
        for fee in COSTS:
            rows=[]
            old=baseline["test"][tag][str(fee)]
            pairs = zip(r.corpus(source,acc),old["rows"],strict=True)
            for (family,bank,law,scene), prev in pairs:
                assert (prev["family"],prev["bank"],prev["law"]) == (family,bank,law)
                focus={"residual":{"gain":0.,"reviews":0.,"changed":0.,"blocked":0.,"enabled":0.},
                       "residual_sampled":{"gain":0.,"reviews":0.,"changed":0.,"blocked":0.,"enabled":0.},
                       "review_flat":{"gain":0.,"reviews":0.,"changed":0.,"blocked":0.,"enabled":0.}}
                for mask in (1,2):
                    vector= features(scene,mask,fee)
                    removed=scene|{"bank":np.r_[scene["bank"][:3],-999.]}
                    assert np.array_equal(vector,features(removed,mask,fee))
                    z = float(vector@weights)
                    actions={"residual":float(z>0), "residual_sampled":float(1/(1+np.exp(-z))),
                             "review_flat":float(original.choose(scene,mask,fee,"review_flat",None)[2])}
                    delta,changed,before,after=branch(scene,mask,fee)
                    mass = float(scene["mass"][mask].sum())
                    for name,rate in actions.items():
                        stats=focus[name]
                        stats["gain"]+=rate*delta
                        stats["reviews"]+=rate*mass
                        stats["changed"]+=rate*mass*changed
                        stats["blocked"]+=rate*mass*(before and not after)
                        stats["enabled"]+=rate*mass*(after and not before)
                for name,stats in focus.items():
                    stats["net"]=prev["outcomes"]["fixed:+7"]["net"]+stats["gain"]
                    assert stats["net"]<=prev["known_joint_ceiling"]+1e-8
                    assert abs(stats["blocked"]+stats["enabled"]-stats["changed"])<=1e-8
                assert abs(focus["review_flat"]["net"]-prev["outcomes"]["review_flat"]["net"])<=1e-8
                rows.append({"family":family,"bank":bank,"law":law,"outcomes":focus})
            overall[tag][str(fee)]={"rows":rows,"summary":r.summarize(rows)}
    return overall


def run():
    torch.set_num_threads(1)
    archive,held=r.point_banks()
    data=r.read(HERE/"review.json")
    groups={}
    for f, prior in data["archive_folds"].items():
        w,trace=fit([row for row in archive if row[0]!=f])
        tests=evaluate([row for row in archive if row[0]==f],prior,w)
        groups[f]={"weights":w.tolist(),"objective":trace,"test":tests}
    w,trace=fit(archive)
    transfer={"weights":w.tolist(),"objective":trace,"test":evaluate(held,data["transfer"],w)}
    macro={}
    for tag,fee in product(("matched","stressed"),COSTS):
        rows=[g["test"][tag][str(fee)]["summary"] for g in groups.values()]
        macro[f"{tag}/{fee}"]={name:{metric:mean(row[name][metric] for row in rows)
                                  for metric in values} for name,values in rows[0].items()}
    files=(Path(__file__),HERE/"review.json",Path(original.__file__),HERE/"residual-review-protocol.md")
    return {"archive_macro":macro,"archive_folds":groups,"transfer":transfer,
            "sha256":{p.name:r.digest(p) for p in files}}


if __name__ == "__main__":
    print(r.json.dumps(run(),indent=2))
