"""Plan dialogue under known second-turn availability and optional verified answers."""
from collections import Counter
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import crossplay as prior
import delayed as d

s, E = d.s, d.E
ASK, SEND, TOL = d.ASK, d.SEND, d.TOL
QUERIES, ROLES = d.QUERY, d.ROLES
QUERY_ROLES = tuple(ROLES.index(role) for role,_ in QUERIES)
RATES = (.08, .80)


def policy(menu, tree, rate, availability, learned, weights):
    context, _, _ = s.fixture(menu,tree,rate)
    objective="learned" if learned else "record"

    @lru_cache(maxsize=None)
    def second(state):
        _, _, data = context(state)
        best,best_value=None,0.
        for i,branches in enumerate(data):
            probability=availability[QUERY_ROLES[i]]
            value=-ASK+probability*sum(
                b["probability"]*max(0., rate*b[objective]-SEND) for b in branches.values()
            )
            if value>best_value+TOL:
                best,best_value=i,value
        return best,best_value

    @lru_cache(maxsize=None)
    def continuation(state, querying_role, permitted):
        choice,gain=second(state)
        if choice is None or QUERY_ROLES[choice] != querying_role:
            return gain
        _,_,data=context(state)
        sign=QUERIES[choice][1] in permitted
        value=rate*data[choice][sign][objective]-SEND
        return availability[querying_role]*max(0., value)-ASK

    @lru_cache(maxsize=None)
    def first_sends(state, choice, permitted):
        role=QUERY_ROLES[choice]
        sign=QUERIES[choice][1] in permitted
        _,_,data=context(state)
        extra=rate*data[choice][sign][objective]
        next_state=s.advance(state,choice,sign)
        future=rate*(continuation(next_state,role,permitted)-continuation(state,role,permitted))
        gain=extra+future-SEND
        return (d.dot((1.,extra,future),weights) if learned else gain)>TOL

    @lru_cache(maxsize=None)
    def first(state):
        _,_,data=context(state)
        _,no_receipt=second(state)
        probabilities=s.r.a.role_candidates(menu,s.get_log(state))
        best,best_value=None,no_receipt
        for choice,(role,option) in enumerate(QUERIES):
            role_index=QUERY_ROLES[choice]
            candidates=probabilities[role]
            total=0.
            for condition in candidates:
                permitted=tuple(sorted(s.r.a.accepted(menu,condition)))
                sign=option in permitted
                if first_sends(state,choice,permitted):
                    new=s.advance(state,choice,sign)
                    total+=rate*(data[choice][sign][objective]+second(new)[1])+(1-rate)*no_receipt-SEND
                else:
                    total+=no_receipt
            value=total/len(candidates)-ASK
            if value>best_value+TOL:
                best,best_value=choice,value
        return best,best_value

    def replay(state,truth,actual_availability=None):
        channel=availability if actual_availability is None else actual_availability
        marker,base_points,data=context(state)
        choice,_=first(state)

        def ending(current):
            query,_=second(current)
            action,points,branches=context(current)
            metric=Counter(points=points,proof=float(action!="UNRESOLVED"),
                           questions=0.,sends=0.,cost=0.,known_unavailable_questions=0.)
            if query is not None:
                branch=branches[query][truth[query]]
                available=channel[QUERY_ROLES[query]]
                sent=available*(rate*branch["record"]-SEND>TOL)
                metric.update(points=sent*rate*branch["record"],proof=sent*rate*branch["decision"],
                              questions=1.,sends=sent,cost=ASK+SEND*sent,
                              known_unavailable_questions=float(available==0.))
            return metric

        if choice is None:
            result=ending(state)
        else:
            role=QUERY_ROLES[choice]
            permitted=tuple(q for i,(_,q) in enumerate(QUERIES) if QUERY_ROLES[i]==role and truth[i])
            send=first_sends(state,choice,permitted)
            chance=rate*send
            landed=ending(s.advance(state,choice,truth[choice]))
            lost=ending(state)
            result=Counter({key:chance*landed[key]+(1-chance)*value for key,value in lost.items()})
            result.update(questions=1.,sends=float(send),cost=ASK+SEND*send)
        result["record_gain"]=result.pop("points")-base_points
        result["proof_gain"]=result.pop("proof")-float(marker!="UNRESOLVED")
        result["net"]=result["record_gain"]-result["cost"]
        return result

    return first, second, replay


def run():
    bench=s.r.BENCH
    config=E.read(bench/"case.json")
    tree=E.read(bench/"transfer-fit.json")["tree"]
    fit=E.read(HERE.parent/"delayed.json")
    weights=fit["weights"]
    results={}
    for rate in RATES:
        results[str(rate)]={}
        for name, availability in prior.SWAPS.items():
            menu=config["menu"]
            get,old=d.stage(menu,tree,rate,availability=availability,believed_availability=availability)
            learned=policy(menu,tree,rate,availability,True,weights)
            exact=policy(menu,tree,rate,availability,False,weights)
            stats={label:Counter() for label in ("frozen_chair","adaptive_learned","adaptive_exact")}
            _,chosen,_=s.fixture(menu,tree,rate)
            choices={}
            repeats=0
            for world in config["worlds"]:
                for state,truth in d.all_states(world,menu):
                    item=get(state,truth)
                    prev=old(state,item,"fitted",weights)
                    unavailable_turns=0.
                    if item:
                        role, option=item["query"]
                        q=QUERIES.index((role,option))
                        p=rate*prev["first_send"]
                        for frequency, next_state in (
                            (p,s.advance(state,q,truth[q])),(1-p,state)
                        ):
                            last,_=chosen(next_state,1,"learned")
                            if last is not None:
                                unavailable_turns+=frequency*(availability[QUERY_ROLES[last]]==0.)
                    prev["known_unavailable_questions"]=unavailable_turns
                    stats["frozen_chair"].update({k:v for k,v in prev.items() if k not in ("first_send","first_query")})
                    projected=(learned[0](state)[0],exact[0](state)[0])
                    if state in choices:
                        assert choices[state]==projected
                        repeats+=1
                    choices[state]=projected
                    stats["adaptive_learned"].update(learned[2](state,truth))
                    stats["adaptive_exact"].update(exact[2](state,truth))
            assert stats["adaptive_learned"]["known_unavailable_questions"]==0.
            assert stats["adaptive_exact"]["known_unavailable_questions"]==0.
            results[str(rate)][name]={"availability":availability,"arms":stats,"repeated_state_checks":repeats}
    files=(Path(__file__),HERE/"protocol.md",HERE.parent/"delayed.json",bench/"case.json",bench/"transfer-fit.json")
    return {"results":results,"sha256":{p.name:sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__=="__main__":
    E.emit(run())
