"""Learn only retry values that depend on a hidden combined-document score."""
from collections import Counter
from itertools import product
from functools import lru_cache
from pathlib import Path
from statistics import mean

import numpy as np
import torch

import hint_bound as hint

r, HERE = hint.r, hint.HERE
ARMS = ("learned_greedy","learned_sampled",*(f"fixed:{k:+g}" for k in r.SHIFTS))


@lru_cache(maxsize=None)
def reference(preview):
    bank = [*preview, 0.]
    proxy = r.make(bank,"Independent",.85)
    proxy["mass"] = (proxy["mass"] + r.make(bank,"Anticorrelated",.85)["mass"])/2
    empty = hint.solve(proxy,r.HINT)["masks"][0]
    assert empty["hint_mass"] >= 0.
    return empty,proxy


def inputs(scene,mask):
    bank = scene["bank"]
    missing = 3^mask
    x = [1.,(bank[missing]-bank[0])/14,(bank[mask]-bank[0])/14,bank[0]/70,
         float(bank[mask]==0)]
    return np.asarray(x)


def fit(rows):
    archive = r.corpus(rows,.85)
    total = Counter(site for site,_,_,_ in archive)
    matrix, values, mass = [],[],[]
    for site,_,_,scene in archive:
        for mask in (1,2):
            state = scene["mass"][mask].sum(axis=1)
            marginal = scene["score"][mask,:,1+(mask==1)] - scene["score"][mask,:,0]
            matrix.append(inputs(scene,mask))
            values.append(float(state @ marginal)/(len(total)*total[site]))
            mass.append(float(state.sum())/(len(total)*total[site]))
    matrix, values = np.array(matrix),np.array(values)
    w = np.zeros(matrix.shape[1])
    def objective(w):
        p = 1/(1+np.exp(-matrix@w))
        return float(p @ values), matrix.T@(p*(1-p)*values)-r.PENALTY*w
    initial,grad = objective(w)
    for j,d in enumerate(np.eye(len(w))*1e-5):
        assert abs((objective(w+d)[0]-objective(w-d)[0])/2e-5-grad[j])<1e-9
    for _ in range(r.STEPS):
        _,grad=objective(w)
        w += r.STEP*grad
    final = objective(w)[0]
    assert final>=initial
    return w,[initial,final],sum(mass)


def play(scene,arm,w):
    preview = tuple(scene["bank"][:3])
    empty, proxy = reference(preview)
    p = torch.zeros((4,2,2),dtype=r.D)
    q = torch.zeros((4,4,3),dtype=r.D)
    p[0] = torch.tensor(empty["send_maps"],dtype=r.D)
    q[0,np.arange(4),empty["retry_by_hint"]] = 1.
    q[3,:,0] = 1.
    for mask in (1,2):
        missing = 3^mask
        candidate = 1+(mask==1)
        if arm.startswith("learned"):
            z = inputs(scene,mask) @ w
            probability = float(1/(1+np.exp(-z))) if arm.endswith("sampled") else float(z>0)
        else:
            shift = float(arm.split(":")[1])
            mass = proxy["mass"][mask].sum(axis=1)
            link = r.BINARY[:,candidate-1]
            retry_success = float(mass @ np.where(link,.9,.2)/mass.sum())
            probability = float(retry_success*(preview[missing]-preview[0]+shift)>r.RETRY)
        q[mask,:,candidate] = probability
        q[mask,:,0] = 1-probability
    net,score,tries,hints = [float(v) for v in r.expected(scene,p,q)]
    alternate = r.independent_check(scene,p,q)
    assert max(abs(a-b) for a,b in zip(alternate,(net,score,tries,hints),strict=True))<1e-8
    return {"net":net,"release":score,"retries":tries,"hints":hints}


def evaluate(rows,w,accuracy):
    results = []
    for f, name, law, scene in r.corpus(rows,accuracy):
        hidden = scene | {"bank":np.r_[scene["bank"][:3],-999.]}
        assert all(np.array_equal(inputs(scene,m),inputs(hidden,m)) for m in (1,2))
        details = {arm:play(scene,arm,w) for arm in ARMS}
        upper = hint.solve(scene,r.HINT)["net"]
        assert all(x["net"]<=upper+1e-10 for x in details.values())
        results.append({"family":f,"bank":name,"law":law,"score_bank":scene["bank"].tolist(),
                        "outcomes":details,"paid_hint_ceiling":upper})
    return {"rows":results,"summary":r.summarize(results)}


def trial(fitting, test):
    w,trace,mass = fit(fitting)
    assert not {r1[0] for r1 in fitting} & {r1[0] for r1 in test}
    measured = evaluate(fitting,w,.85)["summary"]
    fixed = max((key for key in measured if key.startswith("fixed")),key=lambda key:measured[key]["net"])
    conditions = {}
    for tag,acc in (("matched",.85),("stressed",.65)):
        checked = evaluate(test,w,acc)
        checked["fixed_net"] = checked["summary"][fixed]["net"]
        conditions[tag] = checked
    return {"training_families":sorted({r1[0] for r1 in fitting}), "weights":w.tolist(),
            "training_objective":trace, "training_single_receipt_probability":mass,
            "fixed_rule":fixed, "test":conditions}


def run():
    torch.set_num_threads(1)
    rows, held = r.point_banks()
    families = sorted({x[0] for x in rows})
    trials = {f:trial([row for row in rows if row[0]!=f],[row for row in rows if row[0]==f])
              for f in families}
    tests = {mode:{
        "learned":mean(t["test"][mode]["summary"]["learned_greedy"]["net"] for t in trials.values()),
        "sampled":mean(t["test"][mode]["summary"]["learned_sampled"]["net"] for t in trials.values()),
        "fixed_selected":mean(t["test"][mode]["fixed_net"] for t in trials.values()),
        "fixed_envelope":max(mean(t["test"][mode]["summary"][arm]["net"] for t in trials.values())
                             for arm in ARMS if arm.startswith("fixed"))
    } for mode in ("matched","stressed")}
    pins = (Path(__file__),HERE/"selective-protocol.md",HERE/"hint-bound.json",HERE/"plan.json",Path(hint.__file__))
    return {"archive_macro":tests,"archive_folds":trials,"transfer":trial(rows,held),
            "sha256":{p.name:r.digest(p) for p in pins}}


if __name__ == "__main__":
    print(r.json.dumps(run(),indent=2))
