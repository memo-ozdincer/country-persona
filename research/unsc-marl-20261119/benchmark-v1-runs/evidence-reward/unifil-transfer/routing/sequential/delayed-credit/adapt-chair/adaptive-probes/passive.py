"""Infer availability from a receipt already produced by the dialogue."""
from collections import Counter
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import probe as p

a, E = p.a, p.E
HERE = Path(__file__).resolve().parent
RATE = p.RATE
MODES = ("keep_prior", "certain_to_send", "model_willingness", "mandatory_assumption")


def update(role, delivery, publicly_willing):
    profile = p.PROFILES
    evidence = [RATE*values[role]*publicly_willing for values in profile]
    likelihood = evidence if delivery else [1-x for x in evidence]
    norm=sum(likelihood)
    assert norm>0.
    return tuple(sum(w*row[i] for w,row in zip(likelihood,profile,strict=True))/norm for i in range(2))


def run():
    bench=a.s.r.BENCH
    config=E.read(bench/"case.json")
    menu=config["menu"]
    tree=E.read(bench/"transfer-fit.json")["tree"]
    weights=E.read(p.HERE.parent.parent/"delayed.json")["weights"]
    init=p.beliefs(p.INITIAL)[1]
    chair=a.policy(menu,tree,RATE,init,True,weights)[1]
    context=a.s.fixture(menu,tree,RATE)[0]
    openings=[r for w in config["worlds"] for r in a.d.all_states(w,menu)]
    cohorts=[]
    for state,truth in openings:
        query,_=chair(state)
        if query is None:
            cohorts.append((-1,0.,False))
            continue
        _,_,branches=context(state)
        choices=branches[query]
        mate=a.QUERY_ROLES[query]
        willingness=sum(row["probability"] for row in choices.values()
                        if RATE*row["record"]-a.SEND>a.TOL)
        actually_sends=RATE*choices[truth[query]]["record"]-a.SEND>a.TOL
        cohorts.append((mate,round(willingness,12),actually_sends))
    counts = Counter(cohorts)

    @lru_cache(maxsize=None)
    def replay(estimate):
        return a.policy(menu,tree,RATE,estimate,True,weights)[2]

    result={}
    for name,actual in p.base.ACTUAL.items():
        gross={mode:0. for mode in MODES}
        evidence={mode:0. for mode in MODES}
        observed_acks=0.
        for (role,willingness,actual_send), count in counts.items():
            chance = RATE*actual[role]*actual_send if role>=0 else 0.
            observed_acks += chance*count/len(openings)
            for mode in MODES:
                for got_receipt,probability in ((True,chance),(False,1-chance)):
                    if not probability:
                        continue
                    apply = role>=0 and (
                        mode=="mandatory_assumption"
                        or mode=="model_willingness" and willingness>0.
                        or mode=="certain_to_send" and willingness==1.
                    )
                    estimate=update(role,got_receipt,1. if mode=="mandatory_assumption" else willingness) if apply else init
                    # If the prior yields provably no willing candidates,
                    # a missing receipt conveys no further availability evidence.
                    mass = probability*count/len(openings)
                    gross[mode]+=mass*mean_net(estimate,actual,replay,tuple(openings))
                    evidence[mode]+=mass*apply
        result[name]={"mean_net_per_future_dialogue":gross,"probability_update":evidence,
                      "probability_initial_receipt":observed_acks}
    files=(Path(__file__),HERE/"passive-protocol.md",HERE.parent/"adaptive.py",HERE/"probe.py",bench/"case.json")
    return {"openings":len(openings),
            "questions":sum(role>=0 for role,_,_ in cohorts),
            "questions_certain_to_send_if_available":sum(role>=0 and w==1. for role,w,_ in cohorts),
            "profiles":result,"sha256":{f.name:sha256(f.read_bytes()).hexdigest() for f in files}}


@lru_cache(maxsize=None)
def mean_net(estimate,actual,replay,openings):
    return p.base.average_gain(replay(estimate),openings,actual)


if __name__=="__main__":
    E.emit(run())
