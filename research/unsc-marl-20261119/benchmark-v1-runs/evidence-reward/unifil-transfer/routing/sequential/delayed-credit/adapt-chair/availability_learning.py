"""Update the planner's availability belief from observable acknowledgment counts."""
from hashlib import sha256
from itertools import product
from math import comb
from pathlib import Path

import adaptive as a

E, s, d = a.E, a.s, a.d
HERE = Path(__file__).resolve().parent
RATE = .8
PROFILES = dict(a.prior.SWAPS)
ACTUAL = PROFILES | {"outside_prior": (.4,.95)}


def likelihood(counts, n, profile):
    p=1.
    for seen, available in zip(counts,profile,strict=True):
        receipt=RATE*available
        p*=comb(n,seen)*receipt**seen*(1-receipt)**(n-seen)
    return p


def posterior(counts,n):
    values=[(profile,likelihood(counts,n,profile)) for profile in PROFILES.values()]
    total=sum(w for _,w in values)
    if total<=0.:
        # The support includes a positive chance of any count sequence.
        raise ValueError("Observed acknowledgments are outside the prior model")
    return tuple(sum(pair[i]*w for pair,w in values)/total for i in range(2))


def average_gain(replay, rows, availability):
    return sum(replay(state,truth,actual_availability=availability)["net"]
               for state,truth in rows)/len(rows)


def run():
    bench=s.r.BENCH
    config=E.read(bench/"case.json")
    tree=E.read(bench/"transfer-fit.json")["tree"]
    weights=E.read(HERE.parent/"delayed.json")["weights"]
    rows=[pair for world in config["worlds"] for pair in d.all_states(world,config["menu"])]
    assert len(rows)==768
    results={}
    for name, actual in ACTUAL.items():
        known = a.policy(config["menu"],tree,RATE,actual,True,weights)[2]
        known_average=average_gain(known,rows,actual)
        prior=posterior((0,0),0)
        existing=a.policy(config["menu"],tree,RATE,prior,True,weights)[2]
        zero=average_gain(existing,rows,actual)
        cases={}
        for n in (0,1,2):
            total=0.
            branches=[]
            for counts in product(range(n+1),repeat=2):
                mass=likelihood(counts,n,actual)
                if not mass:
                    continue
                estimate=posterior(counts,n)
                choose=a.policy(config["menu"],tree,RATE,estimate,True,weights)[2]
                outcome=average_gain(choose,rows,actual)
                total+=mass*outcome
                branches.append({"acks":counts,"probability":mass,
                                 "posterior_availability":estimate,"mean_dialogue_net":outcome})
            assert abs(sum(r["probability"] for r in branches)-1.)<1e-10
            cost=n*(2*a.ASK+a.SEND*sum(actual))
            margin=total-zero
            min_horizon=(int(cost/margin)+1 if margin>1e-10 and n else None)
            cases[str(n)]={"mean_dialogue_net":total,"probing_cost_once":cost,
                           "advantage_per_dialogue_vs_no_probes":margin,
                           "first_profitable_horizon":min_horizon,"branches":branches}
        results[name]={"actual":actual,"known_mean_dialogue_net":known_average,"probes_per_role":cases}
    files=(Path(__file__),HERE/"availability-learning-protocol.md",HERE/"adaptive.py",HERE/"adaptive.json",
           HERE.parent/"delayed.json",bench/"case.json",bench/"transfer-fit.json")
    return {"openings":len(rows),"question_delivery":RATE,"prior_profiles":list(PROFILES),
            "results":results,"sha256":{p.name:sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__=="__main__":
    E.emit(run())
