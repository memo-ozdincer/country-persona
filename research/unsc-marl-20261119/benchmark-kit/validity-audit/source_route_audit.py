"""Compare the fitted senders to new-source and centralized controls."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np

import source_route_fit as fit


def new_source(public, options, available):
    return next((i for i,a in enumerate(options) if a and a&available and not a&public),0)


def evaluate(public,weights,availability,theta):
    features, legal, table = fit.problem(public,weights,availability)
    learned = tuple(np.where(legal,features@theta,-np.inf).argmax(axis=1))
    independent = tuple(max((i for i,allow in enumerate(legal[s]) if allow),
                            key=lambda i: (fit.reward(public|options[i],weights)-fit.MESSAGE_COST*bool(i),-i))
                        for s,options in enumerate(fit.CHOICES))
    novelty = tuple(new_source(public,options,availability[s]) for s,options in enumerate(fit.CHOICES))
    oracle = np.unravel_index(np.where(legal[0,:,None]&legal[1,None,:],table,-np.inf).argmax(),table.shape)
    out={}
    for name,(i,j) in (("learned",learned),("independent",independent),("new_source",novelty),("joint_planner",oracle)):
        sent = fit.CHOICES[0][int(i)],fit.CHOICES[1][int(j)]
        assert legal[0,i] and legal[1,j]
        out[name]={"return":float(table[i,j]),"points":fit.reward(public|sent[0]|sent[1],weights),
                   "blocks":int(bool(sent[0]))+int(bool(sent[1])),"selected":sent}
    return out


def summarize(rows):
    result={}
    for key in rows[0]:
        counts=Counter()
        for row in rows:
            counts.update({k:row[key][k] for k in ("return","points","blocks")})
            counts["planner_ties"] += abs(row[key]["return"] - row["joint_planner"]["return"]) < 1e-8
        result[key]={"mean_return":counts["return"]/len(rows),"mean_proof_points":counts["points"]/len(rows),
                     "mean_messages":counts["blocks"]/len(rows),"planner_ties":counts["planner_ties"]}
    return result


def gradient_check():
    features, legal, rewards = fit.synthetic()
    theta = np.linspace(-.3,.3,features.shape[-1])
    def calc(values):
        p = np.exp(np.where(legal, features @ values,-np.inf))
        p /= p.sum(axis=-1,keepdims=True)
        return p
    def objective(values):
        p = calc(values)
        return np.einsum("ni,nij,nj->",p[:,0],rewards,p[:,1])/len(p)
    p = calc(theta)
    q=np.stack((np.einsum("nij,nj->ni",rewards,p[:,1]),
                np.einsum("nij,ni->nj",rewards,p[:,0])),axis=1)
    analytical=np.einsum("nsa,nsaf->f",p*(q-(p*q).sum(axis=-1,keepdims=True)),features)/len(p)
    eps=1e-5
    numerical=np.array([(objective(theta+d)-objective(theta-d))/(2*eps)
                        for d in np.eye(len(theta))*eps])
    error=float(np.max(np.abs(analytical-numerical)))
    assert error < 1e-7
    return error


def audit(path):
    payload=json.loads(path.read_text())
    theta=np.array(payload["coefficients"])
    related=[]
    for view in payload["sudan"]:
        row=evaluate(view["public_mask"],(7,7,7),(3,12),theta)
        for k in ("learned","independent"):
            assert row[k]["return"]==view["arms"][k]["return"]
        assert row["joint_planner"]["return"]==view["arms"]["oracle"]["return"]
        related.append(row)
    rng=np.random.default_rng(fit.SEED+1)
    private_drop=[]
    for _ in range(256):
        public=int(rng.integers(16))
        weights=tuple(int(i) for i in rng.integers(2,9,size=3))
        availability=(int(rng.choice((1,2,3))),int(rng.choice((4,8,12))))
        private_drop.append(evaluate(public,weights,availability,theta))
    return {"fit_sha256":sha256(path.read_bytes()).hexdigest(),"gradient_max_absolute_error":gradient_check(),
            "sudan":{"masks":len(related),"scores":summarize(related),"both_positions_public":related[5]},
            "synthetic_with_unseen_availability_draws":{"cases":len(private_drop),"scores":summarize(private_drop)}}


if __name__=="__main__":
    print(json.dumps(audit(Path(sys.argv[1])),indent=2))
