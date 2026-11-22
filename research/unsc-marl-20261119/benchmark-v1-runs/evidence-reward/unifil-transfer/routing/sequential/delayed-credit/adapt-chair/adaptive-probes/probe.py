"""Select adaptive acknowledgment probes from synthetic rollout values."""
from functools import lru_cache
from hashlib import sha256
from itertools import product
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import availability_learning as base

a, E = base.a, base.E
RATE = base.RATE
PROFILES = tuple(base.PROFILES.values())
NAMES = tuple(base.PROFILES)
LIMIT = 2
HORIZONS = (1, 5, 20, 100)
INITIAL = (0, 0, 0, 0)  # Desk One attempts/receipts, Desk Two attempts/receipts


def history(state, role, heard):
    idx = 2*role
    return (*state[:idx], state[idx]+1, state[idx+1]+heard, *state[idx+2:])


def beliefs(state):
    scores = []
    for profile in PROFILES:
        likelihood = 1.
        for role, available in enumerate(profile):
            tries, heard = state[2*role:2*role+2]
            p = RATE*available
            likelihood *= p**heard*(1-p)**(tries-heard)
        scores.append(likelihood)
    total = sum(scores)
    assert total>0.
    weights = tuple(x/total for x in scores)
    mean = tuple(sum(p[i]*w for p,w in zip(PROFILES,weights,strict=True)) for i in range(2))
    return weights,mean


def synthetic_menus():
    groups = {}
    fields = ("cadence", "format")
    for world in a.s.r.fitted.typed_worlds():
        names = [k for k in world["menu"][0] if k!="id"]
        assert len(names)==2
        mapping = {k:{v:str(i) for i,v in enumerate(sorted({p[k] for p in world["menu"]}))}
                   for k in names}
        menu = [{"id":o["id"],**{f:mapping[k][o[k]] for f,k in zip(fields,names,strict=True)}}
                for o in world["menu"]]
        typed = [{f:mapping[k][card[k]] for f,k in zip(fields,names,strict=True) if k in card}
                 for card in world["requirements"]]
        original = [a.s.r.a.accepted(world["menu"], card) for card in world["requirements"]]
        assert original == [a.s.r.a.accepted(menu, card) for card in typed]
        signature=E.checksum(menu)
        _, worlds=groups.setdefault(signature,(menu,[]))
        worlds.append({"id":world["id"],"requirements":typed})
    return list(groups.values())


def per_profile(groups, tree, weights, actuals):
    rollout=[]
    total=0
    for menu, worlds in groups:
        rows=[row for world in worlds for row in a.d.all_states(world,menu)]
        rollout.append((menu,rows))
        total+=len(rows)

    @lru_cache(maxsize=None)
    def values(state):
        _,estimated=beliefs(state)
        gains=[0.] * len(actuals)
        for menu,rows in rollout:
            play=a.policy(menu,tree,RATE,estimated,True,weights)[2]
            for i,profile in enumerate(actuals):
                gains[i]+=sum(play(opening,truth,actual_availability=profile)["net"]
                              for opening,truth in rows)
        return tuple(x/total for x in gains)

    return total,values


def select(deploy,horizon):
    @lru_cache(maxsize=None)
    def rollout(state):
        weights,mean=beliefs(state)
        best=None
        value=horizon*sum(w*v for w,v in zip(weights,deploy(state),strict=True))
        for role,available in enumerate(mean):
            if state[role*2]>=LIMIT:
                continue
            p=available*RATE
            heard=rollout(history(state,role,1))[1]
            missing=rollout(history(state,role,0))[1]
            net=p*heard+(1-p)*missing-a.ASK-a.SEND*available
            if net>value+1e-10:
                best,value=role,net
        return best,value

    return rollout


def observed(policy, actual, horizon, held_value):
    def follow(state):
        role,_=policy(state)
        if role is None:
            return (horizon*held_value(state),0.,0.)
        p=RATE*actual[role]
        heard=follow(history(state,role,1))
        missing=follow(history(state,role,0))
        net,cost,questions=(p*x+(1-p)*y for x,y in zip(heard,missing,strict=True))
        return net, cost+a.ASK+a.SEND*actual[role],questions+1.
    gross,fees,number=follow(INITIAL)
    return {"dialogue_return":gross,"probe_cost":fees,"expected_probes":number,"net":gross-fees}


def run():
    bench=a.s.r.BENCH
    config=E.read(bench/"case.json")
    tree=E.read(bench/"transfer-fit.json")["tree"]
    weights=E.read(HERE.parent.parent/"delayed.json")["weights"]
    synthetic=synthetic_menus()
    train_n,development=per_profile(synthetic,tree,weights,PROFILES)
    assert train_n==4096
    actual_names=tuple(base.ACTUAL)
    n,evaluation=per_profile([(config["menu"],config["worlds"])],tree,weights,tuple(base.ACTUAL.values()))
    assert n==768
    fixed=E.read(HERE.parent/"availability-learning.json")["results"]
    report={}
    for horizon in HORIZONS:
        choose=select(development,horizon)
        action,prior_value=choose(INITIAL)
        learned={}
        for idx, name in enumerate(actual_names):
            actual=base.ACTUAL[name]
            measured=observed(choose,actual,horizon,lambda state:evaluation(state)[idx])
            earlier=fixed[name]["probes_per_role"]
            assert abs(evaluation(INITIAL)[idx]-earlier["0"]["mean_dialogue_net"])<1e-9
            baselines={number:horizon*row["mean_dialogue_net"]-row["probing_cost_once"]
                       for number,row in earlier.items()}
            learned[name]={"adaptive":measured,"fixed_net":baselines,
                           "gap_vs_no_probe":measured["net"]-baselines["0"]}
        averages={"adaptive":sum(learned[k]["adaptive"]["net"] for k in NAMES)/len(NAMES)}
        for level in range(3):
            averages[str(level)]=sum(learned[k]["fixed_net"][str(level)] for k in NAMES)/len(NAMES)
        report[str(horizon)]={"first_probe":action,"synthetic_prior_net":prior_value,
                              "held_prior_means":averages,"held_profiles":learned}
    files=(Path(__file__),HERE/"protocol.md",HERE.parent/"availability-learning.json",
           HERE.parent/"adaptive.py",bench/"case.json",bench/"transfer-fit.json",
           a.s.r.a.public.signed.SIGNED/"roster.json")
    return {"synthetic_openings":train_n,"held_openings":n,"results":report,
            "sha256":{p.name:sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__=="__main__":
    E.emit(run())
