"""Replay a purchasable exact score preview for the missing combined record."""
from collections import Counter
from itertools import product
from pathlib import Path
from statistics import mean

import numpy as np
import torch

import selective as s

r, HERE = s.r, s.HERE
FEES = (.25,.75,1.5)
CONTROLS = ("fixed:-7","fixed:+0","fixed:+7","always_review","review_zero","review_flat")
ARMS = ("learned","sampled",*CONTROLS)


def view(scene,mask,fee):
    return np.r_[s.inputs(scene,mask),fee]


def effects(scene,mask,fee):
    bank = scene["bank"]
    # This score is available here only for training targets and simulated service responses.
    p = tuple(bank[:3])
    _, proxy = s.reference(p)
    retry = 1+(mask==1)
    link = r.BINARY[:,retry-1]
    mass = proxy["mass"][mask].sum(axis=1)
    likelihood = float(mass @ np.where(link,.9,.2) / mass.sum())
    verified_retry = likelihood * (bank[3]-bank[mask]) > r.RETRY
    actual = scene["mass"][mask].sum(axis=1)
    gain = float(actual @ (scene["score"][mask,:,retry] - scene["score"][mask,:,0]))
    return np.array([0.,gain,gain*verified_retry-fee*actual.sum()]),retry,verified_retry


def soft(w,x):
    score = x @ w
    p = np.exp(score-score.max())
    return p/p.sum()


def fit(rows):
    scenes = r.corpus(rows,.85)
    count = Counter(row[0] for row in scenes)
    prepared = [(view(scene,mask,fee),
                 effects(scene,mask,fee)[0]/(len(count)*count[family]*len(FEES)))
                 for family,_,_,scene in scenes for mask,fee in product((1,2),FEES)]
    x = np.stack([a for a,_ in prepared])
    y = np.stack([a for _,a in prepared])
    w = np.zeros((x.shape[1],3))
    def objective(w):
        scores = x @ w
        exp = np.exp(scores-scores.max(axis=1,keepdims=True))
        p = exp/exp.sum(axis=1,keepdims=True)
        value = np.sum(y*p,axis=1)
        return float(value.sum()), x.T@(p*(y-value[:,None]))-r.PENALTY*w
    first,grad = objective(w)
    for ij in np.ndindex(w.shape):
        bump = np.zeros_like(w)
        bump[ij] = 1e-5
        assert abs((objective(w+bump)[0]-objective(w-bump)[0])/2e-5-grad[ij])<1e-8
    for _ in range(r.STEPS):
        _,grad = objective(w)
        w += r.STEP*grad
    last = objective(w)[0]
    assert last>=first
    return w,[first,last]


def choose(scene,mask,fee,arm,weights):
    visible = scene["bank"][:3]
    if arm in ("learned","sampled"):
        p = soft(weights,view(scene,mask,fee))
        return p if arm=="sampled" else np.eye(3)[int(p.argmax())]
    if arm=="always_review" or (arm=="review_zero" and min(visible[1:])==0) or (
        arm=="review_flat" and min(visible[1:])<=visible[0]):
        return np.array([0.,0.,1.])
    offset = float(arm.split(":")[1]) if arm.startswith("fixed:") else 7.
    missing = 3^mask
    _, proxy = s.reference(tuple(visible))
    optimistic = visible[missing]-visible[0]+offset
    mass = proxy["mass"][mask].sum(axis=1)
    mean_rate = float(mass @ np.where(r.BINARY[:,missing-1],.9,.2)/mass.sum())
    return np.eye(3)[int(optimistic*mean_rate>r.RETRY)]


def evaluate_scene(scene,fee,weights):
    empty,_ = s.reference(tuple(scene["bank"][:3]))
    p = torch.zeros((4,2,2),dtype=r.D)
    base = torch.zeros((4,4,3),dtype=r.D)
    p[0] = torch.tensor(empty["send_maps"],dtype=r.D)
    base[0,np.arange(4),empty["retry_by_hint"]] = 1.
    base[1:,:,0] = 1.
    silent_tail = float(r.expected(scene,p,base)[0])
    stages = {mask:effects(scene,mask,fee) for mask in (1,2)}
    summaries = {}
    for arm in ARMS:
        q = base.clone()
        audits = 0.
        expected = silent_tail
        for mask,(value,retry,accept) in stages.items():
            probs = choose(scene,mask,fee,arm,weights)
            hidden_removed = scene | {"bank":np.r_[scene["bank"][:3],-999.]}
            assert np.array_equal(probs,choose(hidden_removed,mask,fee,arm,weights))
            audits += float(scene["mass"][mask].sum())*probs[2]
            expected += float(probs @ value)
            probability = probs[1]+probs[2]*accept
            q[mask,:,0], q[mask,:,retry] = 1-probability,probability
        net,raw,retries,hints = [float(v) for v in r.expected(scene,p,q)]
        replay = r.independent_check(scene,p,q)
        assert max(abs(a-b) for a,b in zip(replay,(net,raw,retries,hints),strict=True))<1e-8
        net -= fee*audits
        assert abs(net-expected)<1e-8
        summaries[arm] = {"net":net,"release":raw,"retries":retries,"hints":hints,"reviews":audits}
    ceiling = silent_tail+sum(float(values.max()) for values,_,_ in stages.values())
    assert all(v["net"]<=ceiling+1e-8 for v in summaries.values())
    return summaries,ceiling


def evaluate(rows,w,accuracy):
    results = {}
    for fee in FEES:
        measures = []
        for f,name,law,scene in r.corpus(rows,accuracy):
            arms,limit = evaluate_scene(scene,fee,w)
            measures.append({"family":f,"bank":name,"law":law,"outcomes":arms,"known_joint_ceiling":limit})
        results[str(fee)] = {"rows":measures,"summary":r.summarize(measures)}
    return results


def trial(fitting,test):
    assert not {a[0] for a in fitting}&{a[0] for a in test}
    w,trace = fit(fitting)
    validation=evaluate(fitting,w,.85)
    selected = {fee:max(CONTROLS,key=lambda arm:stats["summary"][arm]["net"])
                for fee,stats in validation.items()}
    frozen = {}
    for label,acc in (("matched",.85),("stressed",.65)):
        data=evaluate(test,w,acc)
        for fee,stats in data.items():
            stats["selected_rule"] = selected[fee]
            stats["selected_net"] = stats["summary"][selected[fee]]["net"]
        frozen[label]=data
    return {"training_families":sorted({x[0] for x in fitting}),"weights":w.tolist(),
            "training_net_improvement":trace,"selected":selected,"test":frozen}


def run():
    torch.set_num_threads(1)
    a,b = r.point_banks()
    expected = r.read(HERE/"plan.json")
    assert r.json.loads(r.json.dumps(r.plan())) == expected
    families=sorted({row[0] for row in a})
    folds = {family:trial([row for row in a if row[0]!=family],[row for row in a if row[0]==family])
             for family in families}
    macro={}
    for label, fee in product(("matched","stressed"),FEES):
        rows = [fold["test"][label][str(fee)] for fold in folds.values()]
        macro[f"{label}/{fee}"] = {"learned":mean(r0["summary"]["learned"]["net"] for r0 in rows),
                     "selected_fixed":mean(row["selected_net"] for row in rows),
                     **{arm:mean(row["summary"][arm]["net"] for row in rows) for arm in CONTROLS},
                     "learned_reviews":mean(row["summary"]["learned"]["reviews"] for row in rows)}
    pins = (Path(__file__),HERE/"review-protocol.md",HERE/"selective.json",HERE/"plan.json",Path(s.__file__))
    return {"archive_macro":macro,"archive_folds":folds,"transfer":trial(a,b),
            "sha256":{p.name:r.digest(p) for p in pins}}


if __name__ == "__main__":
    print(r.json.dumps(run(),indent=2))
