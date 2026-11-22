"""Learn a three-role workshop router from fit-excluded menu structures."""
from collections import Counter
from functools import lru_cache
from hashlib import sha256
from itertools import combinations, permutations, product
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/"unifil-transfer"))
from transfer_fit import fit, predict

WORLDS=tuple(product((0,1),repeat=3))
EMPTY=(-1,)*3
FEE=.075
TOL=1e-10
TRAIN=((.55,.75,.95),(.90,.70,.50),(.8,.8,.8))
HELD=((.9,.9,.9),(.90,.80,.35),(.35,.93,.72))
MODES=("fixed","greedy","learned","exact")
DEPTH=8


def read(path):
    return json.loads(path.read_text())


def options(menu,state):
    return [m for m in menu if all(v == -1 or v == actual for v,actual in zip(state,m,strict=True))]


def write_bit(state, role, bit):
    assert state[role] in (-1,bit)
    return state[:role]+(bit,)+state[role+1:]


def terminal(menu,state):
    remaining=options(menu,state)
    if not remaining:
        return "IMPASSE",.8 if -1 in state else 1.
    return ("ABCD"[menu.index(remaining[0])],1.) if -1 not in state else ("UNRESOLVED",0.)


def shape(menu):
    return min(tuple(sorted(tuple(row[i]^f for i,f in zip(order,flip,strict=True)) for row in menu))
               for order in permutations(range(3)) for flip in WORLDS)


def observed(menu,state,delivery,role,budget):
    here=terminal(menu,state)[1]
    branches=[write_bit(state,role,bit) for bit in (0,1)]
    child=tuple(sorted((terminal(menu,x)[1],len(options(menu,x))/4) for x in branches))
    rates=sorted(delivery[i] for i,v in enumerate(state) if v==-1 and i!=role)
    return (budget/3, state.count(-1)/3, here, delivery[role], *([0.]*(2-len(rates))+rates),
            child[0][0],child[0][1],child[1][0],child[1][1])


def solver(menu,delivery):
    @lru_cache(maxsize=None)
    def best(state,horizon):
        actions=values(state,horizon)
        query=max(actions,key=actions.get) if actions else None
        return (query,actions[query]) if query is not None and actions[query]>TOL else (None,0.)

    def values(state,horizon):
        if not horizon:
            return {}
        base=terminal(menu,state)[1]
        after_loss=best(state,horizon-1)[1]
        result={}
        for role,v in enumerate(state):
            if v!=-1:
                continue
            nexts=[write_bit(state,role,bit) for bit in (0,1)]
            got=sum(terminal(menu,x)[1]-base+best(x,horizon-1)[1] for x in nexts)/2
            result[role]=delivery[role]*got+(1-delivery[role])*after_loss-FEE
        return result

    return best,values


def select(mode,state,budget,menu,delivery,exact,tree):
    rows=[i for i,v in enumerate(state) if v==-1]
    if not rows or budget==0:
        return None
    if mode=="fixed":
        return rows[0]
    if mode=="exact":
        return exact(state,budget)[0]
    if mode=="greedy":
        return exact(state,1)[0]
    margins=[(predict(tree,observed(menu,state,delivery,r,budget)),r) for r in rows]
    gain,role=max(margins,key=lambda pair:(pair[0],-pair[1]))
    return role if gain>TOL else None


def replay(menu,delivery,truth,mode,budget,tree):
    exact,_=solver(menu,delivery)

    @lru_cache(maxsize=None)
    def play(state,left):
        query=select(mode,state,left,menu,delivery,exact,tree)
        if query is None:
            decision,credit=terminal(menu,state)
            answer=terminal(menu,truth)[0]
            assert decision in (answer,"UNRESOLVED")
            return (credit,float(decision==answer),0.)
        chance=delivery[query]
        yes=play(write_bit(state,query,truth[query]),left-1)
        no=play(state,left-1)
        merged=[chance*p+(1-chance)*q for p,q in zip(yes,no,strict=True)]
        merged[2]+=1.
        return merged

    credit,passed,questions=play(EMPTY,budget)
    return {"documentary_proxy":credit,"mechanical_accuracy":passed,"expected_questions":questions,
            "net":credit-FEE*questions}


def run():
    case=read(HERE/"case.json")
    menu=tuple(tuple(m) for m in case["packages"].values())
    excluded=shape(menu)
    training=[m for m in combinations(WORLDS,4) if shape(m)!=excluded]
    samples=Counter()
    for synthetic, delivery in product(training,TRAIN):
        _,actions=solver(synthetic,delivery)
        for state,budget in product(product((-1,0,1),repeat=3), range(1,4)):
            for query, label in actions(state,budget).items():
                features=observed(synthetic,state,delivery,query,budget)
                samples[features,round(label,10)]+=1
    tree=fit([(features,goal,n) for (features,goal),n in sorted(samples.items())],DEPTH)
    scores={}
    for delivery,budget in product(HELD,range(1,4)):
        results={mode:Counter() for mode in MODES}
        outcomes={}
        for world in WORLDS:
            rows={mode:replay(menu,delivery,world,mode,budget,tree) for mode in MODES}
            outcomes["".join(map(str,world))]=rows
            for mode,result in rows.items():
                results[mode].update({name:score/len(WORLDS) for name,score in result.items()})
        assert all(results["exact"]["net"]+1e-9>=row["net"] for row in results.values())
        scores[f"{delivery}/{budget}"]={"average":results,"worlds":outcomes}
    files=(Path(__file__),HERE/"case.json",HERE/"protocol.md",
           HERE/case["evidence"],HERE/case["linkage"],
           HERE.parent/"unifil-transfer/transfer_fit.py")
    return {"learned_tree":tree,"synthetic_menus":len(training),"held_menu_equivalent_menus_excluded":70-len(training),
            "training_rows":sum(samples.values()),"results":scores,
            "sha256":{p.name:sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__=="__main__":
    print(json.dumps(run(),indent=2))
