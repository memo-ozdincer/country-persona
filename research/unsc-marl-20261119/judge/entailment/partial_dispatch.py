"""Test routing while retaining confident individual predictions as provisional signs."""
import argparse
from collections import Counter
from itertools import product
import json
from pathlib import Path

from package_panel import inputs, project, source_paths, guarded, restore
from episode import judge, readout
from environment import claim, options_for, record, routing_prior, terminal


def first_bit(pools, order):
    for idx in order:
        pool = pools[idx]
        if pool:
            return pool & -pool
    return 0


def simulate(case, opening, signed, truth, mode, policy, handoff_on_accept=False):
    labels = [o["id"] for o in case["options"]]
    roles = case["roles"]
    full = (1 << len(labels))-1
    positive = [pair[0] for pair in signed]
    known = [pair[0] | pair[1] for pair in signed]
    state, role = (0,0,0,0), 1
    claims, events = [], []

    def submit(i, bit, step):
        nonlocal state
        letter = labels[bit.bit_length()-1]
        if not (known[i] & bit):
            events.append({"step":step, "role":i, "package":letter, "status":"unknown"})
            return False
        predicted = bool(positive[i] & bit)
        actual = bool(truth[i] & bit)
        raw = json.dumps({"stance":"accept" if predicted else "exclude","option":letter})
        status, claim = judge(raw, roles[i], letter, actual, f"claim-{len(claims)+1}")
        events.append({"step":step, "role":i, "package":letter, "status":status})
        if not claim:
            # A rejected prediction withdraws this proposal. It supplies no
            # evidence for the opposite sign.
            known[i] &= ~bit
            positive[i] &= ~bit
            return False
        claims.append(claim)
        state = record(state, i, bit, actual)
        return True

    for i, option in enumerate(opening):
        submit(i, 1<<labels.index(option), i-2)
    for step in range(len(labels)):
        if terminal(state,full):
            break
        local = positive[role]
        if mode=="learned":
            _, actions, chosen = policy(positive,state,role,step,full)
            bit, _, next_role = actions[chosen] if actions else (0,state,1-role)
        else:
            bit = claim(local,state,role,step,full,flex=True)
            after = record(state,role,bit,bool(local&bit)) if bit else state
            next_role = routing_prior(local,after,role,full)
        if not bit & known[role] or mode=="retain_exclusions":
            groups = tuple(bits & known[role] for bits in options_for(local,state,role,full))
            order = (0,3,1,2) if mode=="retain_exclusions" else (0,1,2,3)
            bit = first_bit(groups, order)
            after = record(state,role,bit,bool(local&bit)) if bit else state
            if mode=="retain_exclusions":
                more_exclusions = (after[1] | after[3]) & full
                remaining_known = known[role] & ~local & ~more_exclusions & full
                next_role = role if bit and remaining_known else 1-role
            else:
                next_role = routing_prior(local,after,role,full) if bit else 1-role
        if bit:
            if handoff_on_accept and local & bit:
                next_role = 1-role
            role = next_role if submit(role,bit,step) else 1-role
        else:
            events.append({"step":step,"role":role,"status":"pass"})
            role=1-role
    proof=readout(labels,roles,claims)
    return {"claims":claims,"events":events,"readout":proof}


def evaluate(metrics, handoff_on_accept=False):
    choose = guarded(restore(json.loads(source_paths()["policy"].read_text())))
    counts, rows = Counter(), {}
    for family, case, task in inputs():
        labels = [item["id"] for item in case["options"]]
        truth = tuple(project(case["options"], card["expected"]) for card in task["cards"])
        signed = []
        for actor in (0,1):
            option_labels = [metrics["decisions"][f"{family}/{actor}/{p}"]["accept"] for p in labels]
            signed.append(tuple(sum(1<<i for i,x in enumerate(option_labels) if x is flag) for flag in (True,False)))
        starts = product(*([label for i,label in enumerate(labels) if real & (1<<i)] for real in truth))
        expectation = "AGREEMENT_POSSIBLE" if task["outcome"]=="agreement" else "IMPASSE"
        for opening in starts:
            for mode in ("script","learned","retain_exclusions"):
                answer = simulate(case,opening,signed,truth,mode,choose,handoff_on_accept)
                counts[family,mode,"tested"] += 1
                counts[family,mode,"certified"] += answer["readout"]["state"]==expectation
                counts[family,mode,"unknown_openings"] += sum(
                    c["step"]<0 and c["status"]=="unknown" for c in answer["events"])
                rows["/".join((family,mode,"".join(opening)))]=answer
    return {"counts":{"/".join(key):v for key,v in counts.items()},"traces":rows}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("metrics",type=Path)
    args=p.parse_args()
    print(json.dumps(evaluate(json.loads(args.metrics.read_text())),indent=2))
