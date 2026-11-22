"""Joint policy gradients over private-link hints and one documentary retry."""
import argparse
from collections import Counter
from itertools import product
import json
from pathlib import Path
from statistics import mean

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
STUDY = RUNS.parent
WRITERS = STUDY / "benchmark-kit/reader-use/writer-aware-bundles/results.json"
MYANMAR = RUNS / "myanmar-frozen-admission/mechanism.json"
REDSEA = RUNS / "reporting-2739/learned-admission/documentary-replay/supplement-results.json"
STEPS, STEP, PENALTY = 200, .06, .01
HINT, RETRY = .15, .75
SHIFTS = (-7., 0., 7.)
FAMILIES = ("Independent", "Anticorrelated")
STATE = tuple(product(range(2), repeat=2))
BINARY = np.array(STATE)
MISSING = np.array([[(mask & (1 << i)) == 0 for i in range(2)] for mask in range(4)])
ARMS = ("silent", *(f"{hint}:{shift:+g}" for hint, shift in product(("none","good","weak"),SHIFTS)),
        "full_bank", "full_bank_and_signal")
D = torch.float64


def read(path):
    return json.loads(path.read_text())


def digest(path):
    from hashlib import sha256
    return sha256(path.read_bytes()).hexdigest()


def point_banks():
    rows = []
    for item in read(WRITERS)["banks"]:
        if item["family"] == "myanmar":
            continue
        for anchor in (1, 2, 4):
            u,v = [bit for bit in (1,2,4) if bit!=anchor]
            scores = item["release"]
            rows.append((item["family"], f'{item["mode"]}/{anchor}',
                         [scores[anchor | extra] for extra in (0,u,v,u|v)]))
    held = []
    for family, location in (("myanmar", MYANMAR), ("reporting-2739", REDSEA)):
        grades = read(location)["records"]
        first = [grades[f"0/consensus/{i}"]["score"]["released_70"] for i in range(4)]
        assert [grades[f"1/consensus/{i}"]["score"]["released_70"] for i in range(4)] == first
        held.append((family,"literal",first))
    return rows, held


def plan():
    sources = (Path(__file__), HERE/"protocol.md", WRITERS, MYANMAR, REDSEA)
    archive, held = point_banks()
    return {"banks": archive, "transfer": held, "steps": STEPS, "step":STEP, "penalty":PENALTY,
            "costs":[HINT,RETRY], "fit_signal_accuracy":.85, "stress_signal_accuracy":.65,
            "hashes":{str(p.relative_to(STUDY)): digest(p) for p in sources}}


def prior(label):
    return np.array([.25] * 4 if label == "Independent" else [.075,.425,.425,.075])


def features(bank, mask):
    gain = [(bank[1<<i]-bank[0])/14 for i in range(2)]
    own = np.array([[1., (sig-.5)*2, gain[i], gain[1-i], float(not MISSING[mask,1-i])]
                    for i,sig in product(range(2),range(2))]).reshape(2,2,5)
    chair = np.array([[1.,gain[i],gain[1-i],float(not MISSING[mask,1-i]),bits[i],bits[1-i]]
                      for bits,i in product(STATE,range(2))]).reshape(4,2,6)
    return own,chair


def make(bank, law, accuracy):
    bank = np.asarray(bank,dtype=float)
    chance = np.array([.4,.8])
    again = np.array([.2,.9])
    posterior_mass = np.zeros((4,4,4))
    payoff = np.zeros((4,4,3))
    for mask, k in product(range(4),range(4)):
        good = BINARY[k]
        observed = ~MISSING[mask]
        p_mask = np.prod(np.where(observed, chance[good],1-chance[good]))
        for j, sig in enumerate(BINARY):
            posterior_mass[mask,k,j] = prior(law)[k] * p_mask * np.prod(np.where(sig==good,accuracy,1-accuracy))
        payoff[mask,k,0] = bank[mask]
        for i in range(2):
            payoff[mask,k,1+i] = bank[mask] + again[good[i]] * (bank[mask | 1<<i] - bank[mask]) - RETRY
    assert abs(posterior_mass.sum()-1)<1e-10
    legal = np.column_stack((np.ones(4,dtype=bool),MISSING))
    nominees = np.array([np.all(~bits.astype(bool) | MISSING[mask]) for mask,bits in product(range(4),BINARY)]).reshape(4,4)
    sender, chair = zip(*(features(bank,m) for m in range(4)),strict=True)
    return {"bank":bank,"mass":posterior_mass,"score":payoff,"sender":np.array(sender),"chair":np.array(chair),
            "legal":legal,"nominees":nominees}


def strategy(scene, w, greedy=False):
    sender, chair = w
    p = torch.sigmoid(torch.as_tensor(scene["sender"]) @ sender)
    z = torch.as_tensor(scene["chair"]) @ chair
    z = torch.cat((torch.zeros_like(z[...,:1]),z),dim=-1)
    q = torch.softmax(z.masked_fill(~torch.as_tensor(scene["legal"])[:,None,:],-torch.inf), dim=-1)
    if greedy:
        p = (p > .5).to(D)
        q = torch.nn.functional.one_hot(q.argmax(-1),3).to(D)
    p = p * torch.as_tensor(MISSING)[:,:,None]
    return p, q


def expected(scene,p,q):
    probabilities = []
    for signals in BINARY:
        probs = torch.stack([p[:,i,s] for i,s in enumerate(signals)],dim=1)
        joint = torch.stack([torch.prod(torch.where(torch.as_tensor(bits.astype(bool)),probs,1-probs),dim=1)
                             for bits in BINARY],dim=1)
        probabilities.append(joint)
    pm = torch.stack(probabilities,dim=1)
    assert torch.allclose(pm.sum(-1),torch.ones((4,4),dtype=D))
    mass = torch.as_tensor(scene["mass"])
    leaf = torch.einsum("mkj,mjf,mfa->mkfa",mass,pm,q)
    assert abs(float(leaf.sum().detach())-1)<1e-10
    points = torch.sum(leaf*torch.as_tensor(scene["score"])[:,:,None,:])
    hints = torch.einsum("mkf,f->",leaf.sum(-1),torch.as_tensor(BINARY.sum(-1),dtype=D))
    retries = leaf[...,1:].sum()
    return points-HINT*hints, points+RETRY*retries, retries, hints


def policy_fixed(scene, name):
    mode, shift = name.split(":") if ":" in name else (name,"0")
    shift = float(shift)
    p = torch.zeros((4,2,2),dtype=D)
    if mode in ("good","weak"):
        p[:,:,int(mode=="good")] = torch.as_tensor(MISSING)
    q = torch.zeros((4,4,3),dtype=D)
    bank = scene["bank"]
    marg = np.array([bank[1]-bank[0],bank[2]-bank[0]])
    for mask, k in product(range(4),range(4)):
        signals = BINARY[k]
        signal_rows = ([k] if mode=="full_bank_and_signal" else np.where(
            np.all(np.where(MISSING[mask], BINARY if mode=="good" else 1-BINARY, 0) == signals,axis=1))[0]
            if mode in ("good","weak") else range(4))
        weights = scene["mass"][mask][:,list(signal_rows)].sum(axis=1)
        if not scene["nominees"][mask,k] or not weights.sum() or mode=="silent":
            q[mask,k,0] = 1
            continue
        success = (weights @ np.where(BINARY,.9,.2))/weights.sum()
        if mode.startswith("full_bank"):
            delta = [bank[mask|1<<i]-bank[mask] for i in range(2)]
        else:
            delta = [marg[i]+shift*float(not MISSING[mask,1-i]) for i in range(2)]
        score = np.r_[0.,np.where(MISSING[mask],success*delta-RETRY,-np.inf)]
        q[mask,k,int(score.argmax())] = 1
    return p, q


def semantic_oracle(scene):
    gains = []
    for mask,sig in product(range(4),range(4)):
        outcome = scene["mass"][mask,:,sig] @ scene["score"][mask]
        gains.append(float(np.where(scene["legal"][mask],outcome,-np.inf).max()))
    return sum(gains)


def corpus(rows, accuracy):
    return [(family,name,law,make(b,law,accuracy))
            for family, name, bank in rows for law in FAMILIES
            for b in (bank,[bank[0],bank[2],bank[1],bank[3]])]


def fit(rows):
    train = corpus(rows,.85)
    counts = Counter(r[0] for r in train)
    scene = {key:torch.as_tensor(np.stack([r[3][key] for r in train]))
             for key in ("sender","chair","mass","score","legal")}
    family = torch.tensor([1/(len(counts)*counts[r[0]]) for r in train],dtype=D)
    weights = [torch.zeros(k,dtype=D,requires_grad=True) for k in (5,6)]
    bits = torch.as_tensor(BINARY.astype(bool))
    hint_cost = torch.as_tensor(BINARY.sum(-1)*HINT,dtype=D)
    payoff = scene["score"][:,:,:,None,:] - hint_cost[None,None,None,:,None]

    def objective():
        p = torch.sigmoid(scene["sender"] @ weights[0]) * torch.as_tensor(MISSING)[:,:,None]
        by_signal = torch.stack([p[:,:,i,BINARY[:,i]] for i in range(2)],dim=-1)
        hints = torch.prod(torch.where(bits,by_signal[:,:,:,None,:],1-by_signal[:,:,:,None,:]),dim=-1)
        z = scene["chair"] @ weights[1]
        z = torch.cat((torch.zeros_like(z[...,:1]),z),dim=-1)
        q = torch.softmax(z.masked_fill(~scene["legal"][:,:,None,:],-torch.inf),dim=-1)
        leaf = torch.einsum("nmkj,nmjf,nmfa->nmkfa",scene["mass"],hints,q)
        assert torch.allclose(leaf.sum(dim=(1,2,3,4)),torch.ones(len(train),dtype=D))
        return family @ (leaf*payoff).sum(dim=(1,2,3,4))

    with torch.no_grad():
        single = sum(expected(s,*strategy(s,weights))[0]*f for (_,_,_,s),f in zip(train,family,strict=True))
        assert torch.allclose(single,objective(),atol=1e-10,rtol=0)
    start = float(objective().detach())
    for _ in range(STEPS):
        net = objective() - PENALTY * sum((w*w).sum() for w in weights)/2
        gradients = torch.autograd.grad(net,weights)
        with torch.no_grad():
            for w, grad in zip(weights,gradients,strict=True):
                assert torch.isfinite(grad).all()
                w += STEP*grad
    end = float(objective().detach())
    assert end>=start
    return [w.detach() for w in weights], [start,end]


def summarize(rows):
    families = Counter(r["family"] for r in rows)
    keys = rows[0]["outcomes"].keys()
    return {arm:{metric:sum(r["outcomes"][arm][metric]/(len(families)*families[r["family"]]) for r in rows)
                 for metric in rows[0]["outcomes"][arm]} for arm in keys}


def independent_check(scene,p,q):
    net, released, tries, hints = 0., 0., 0., 0.
    sends, actions = p.detach().numpy(), q.detach().numpy()
    for mask,k,j in product(range(4),repeat=3):
        mass = scene["mass"][mask,k,j]
        pair = [sends[mask,i,ix] for i,ix in enumerate(BINARY[j])]
        for f,bits in enumerate(BINARY):
            path = mass * np.prod([p if b else 1-p for p,b in zip(pair,bits,strict=True)])
            for a, chance in enumerate(actions[mask,f]):
                branch = path*chance
                tries += branch*(a!=0)
                hints += branch*sum(bits)
                base = scene["bank"][mask]
                result = base if a==0 else base + (.9 if BINARY[k,a-1] else .2) * (
                    scene["bank"][mask | 1<<(a-1)]-base)
                net += branch*(result-RETRY*(a!=0)-HINT*sum(bits))
                released += branch*result
    return net,released,tries,hints


def evaluate(rows, weights, accuracy):
    results = []
    for family,name,law,scene in corpus(rows,accuracy):
        outcomes = {}
        reference = {arm:policy_fixed(scene,arm) for arm in ARMS if arm!="full_bank_and_signal"}
        reference |= {"learned_greedy":strategy(scene,weights,True), "learned_sampled":strategy(scene,weights)}
        for arm,(p,q) in reference.items():
            net,points,retries,hints = [float(v) for v in expected(scene,p,q)]
            assert abs(net - points + retries*RETRY + hints*HINT)<1e-8
            if arm in ("learned_greedy","learned_sampled","full_bank","silent"):
                independently = independent_check(scene,p,q)
                assert max(abs(a-b) for a,b in zip(independently,(net,points,retries,hints),strict=True))<1e-8
            outcomes[arm] = {"net":net,"release":points,"retries":retries,"hints":hints}
        limit = semantic_oracle(scene)
        assert all(v["net"] <= limit+1e-8 for v in outcomes.values())
        results.append({"family":family,"bank":name,"law":law,"scores":scene["bank"].tolist(),
                        "outcomes":outcomes,"free_signal_full_bank_ceiling":limit})
    return results


def choose(rows, weights):
    fit_rows = evaluate(rows,weights,.85)
    measures = summarize(fit_rows)
    return max([arm for arm in ARMS if not arm.startswith("full_bank")],key=lambda arm:measures[arm]["net"])


def run():
    assert json.loads(json.dumps(plan()))==read(HERE/"plan.json")
    torch.set_num_threads(1)
    train, held = point_banks()
    fit_groups = {}
    for name in sorted({row[0] for row in train})+["transfer"]:
        fitting = [r for r in train if r[0]!=name]
        testing = held if name=="transfer" else [r for r in train if r[0]==name]
        assert not {r[0] for r in fitting}&{r[0] for r in testing}
        weights, trace = fit(fitting)
        fixed = choose(fitting,weights)
        results = {}
        for tag,accuracy in (("matched",.85),("stressed",.65)):
            rows = evaluate(testing,weights,accuracy)
            metrics = summarize(rows)
            results[tag] = {"rows":rows,"summary":metrics, "fixed_net":metrics[fixed]["net"]}
        fit_groups[name] = {"fitting":sorted({r[0] for r in fitting}),"weights":[w.tolist() for w in weights],
                            "training_net":trace,"chosen_fixed":fixed,"test":results}
    return {"groups":fit_groups,"plan_sha256":digest(HERE/"plan.json")}


if __name__ == "__main__":
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument("mode",choices=("plan","run"))
    print(json.dumps({"plan":plan,"run":run}[a.parse_args().mode](),indent=2))
