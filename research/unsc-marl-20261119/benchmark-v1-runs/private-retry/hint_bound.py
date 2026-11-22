"""Enumerate the exact paid hint ceiling and verify its policies."""
from itertools import product
from pathlib import Path
from statistics import mean

import numpy as np
import torch

import retry as r

HERE = r.HERE
FEES = (0., .15, .30)
CONSTANT = (0,0)


def solve(scene, fee):
    p = torch.zeros((4,2,2),dtype=r.D)
    q = torch.zeros((4,4,3),dtype=r.D)
    states = []
    for mask in range(4):
        options = [r.STATE if missing else (CONSTANT,) for missing in r.MISSING[mask]]
        mass = scene["mass"][mask]
        score = scene["score"][mask]
        marginals = mass.sum(axis=0)
        legal = scene["legal"][mask]
        baseline = float(np.where(legal, mass.sum(axis=1) @ score, -np.inf).max())
        outcomes = []
        branch_value = mass.T @ score
        for maps in product(*options):
            messages = [2*maps[0][a]+maps[1][b] for a,b in r.STATE]
            posterior = np.zeros((4,3))
            np.add.at(posterior,messages,branch_value)
            replies = np.where(legal,posterior,-np.inf).argmax(axis=1)
            spend = sum(marginals[i] * sum(r.STATE[m]) for i,m in enumerate(messages))
            expected = float(posterior[np.arange(4),replies].sum() - fee*spend)
            outcomes.append((expected,float(spend),maps,replies))
        points, spend, policy, replies = max(outcomes,key=lambda x:(x[0],-x[1]))
        assert points>=baseline-1e-10
        p[mask] = torch.tensor(policy,dtype=r.D)
        q[mask,np.arange(4),replies] = 1.
        states.append({"mask":mask,"conditional_mass":float(mass.sum()),"no_hint":baseline,
                       "optimized":points,"hint_mass":spend,"send_maps":policy,
                       "retry_by_hint":replies.tolist(),"codes_tried":len(outcomes)})
    returned = tuple(float(v) for v in r.expected(scene,p,q))
    checked = r.independent_check(scene,p,q)
    assert all(abs(a-b)<1e-8 for a,b in zip(returned,checked,strict=True))
    net = returned[0]+(r.HINT-fee)*returned[3]
    unpriced = r.semantic_oracle(scene)
    assert abs(net-sum(s["optimized"] for s in states))<1e-9
    assert abs(returned[3]-sum(s["hint_mass"] for s in states))<1e-9
    if fee==0:
        assert abs(net-unpriced)<1e-9
    assert net<=unpriced+1e-9
    baseline = sum(s["no_hint"] for s in states)
    fixed = float(r.expected(scene,*r.policy_fixed(scene,"full_bank"))[0])
    assert abs(baseline-fixed)<1e-9
    return {"net":net,"expected_hints":returned[3],"expected_retries":returned[2],
            "released":returned[1],"free_signal":unpriced,"no_hint":baseline,
            "hint_value":net-baseline,"masks":states}


def summarize(rows):
    families = sorted({x["family"] for x in rows})
    grouped = {f:[r for r in rows if r["family"]==f] for f in families}
    return {str(fee): {
        "no_hint":mean(mean(r["fees"][str(fee)]["no_hint"] for r in group) for group in grouped.values()),
        "net":mean(mean(r["fees"][str(fee)]["net"] for r in group) for group in grouped.values()),
        "value":mean(mean(r["fees"][str(fee)]["hint_value"] for r in group) for group in grouped.values()),
        "positive_cases":sum(r["fees"][str(fee)]["hint_value"]>1e-9 for r in rows),
        "positive_masks":{str(mask):sum(row["fees"][str(fee)]["masks"][mask]["optimized"] >
                                      row["fees"][str(fee)]["masks"][mask]["no_hint"]+1e-9 for row in rows)
                          for mask in range(4)}
    } for fee in FEES}


def run():
    assert r.json.loads(r.json.dumps(r.plan())) == r.read(HERE/"plan.json")
    torch.set_num_threads(1)
    train, transfer = r.point_banks()
    groups = {}
    for name, banks in (("archive",train),("transfer",transfer)):
        groups[name] = {}
        for case, accuracy in (("matched",.85),("stressed",.65)):
            rows = [{"family":f,"bank":b,"law":law,"preview":scene["bank"].tolist(),
                     "fees":{str(fee):solve(scene,fee) for fee in FEES}}
                    for f,b,law,scene in r.corpus(banks,accuracy)]
            assert all(row["fees"]["0.0"]["net"]+1e-9>=row["fees"]["0.15"]["net"]>=
                       row["fees"]["0.3"]["net"]-1e-9 for row in rows)
            groups[name][case] = {"summary":summarize(rows),"rows":rows}
    pins = (Path(__file__),HERE/"hint-bound-protocol.md",HERE/"plan.json",Path(r.__file__))
    return {"groups":groups,"sha256":{p.name:r.digest(p) for p in pins}}


if __name__ == "__main__":
    print(r.json.dumps(run(),indent=2))
