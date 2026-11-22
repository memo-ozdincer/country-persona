"""Learn whether to send a sign from its effect on the final two-turn record."""
from collections import Counter
from functools import lru_cache
from hashlib import sha256
from itertools import product
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import sequential as s

E, QUERY, ROLES = s.E, s.QUERIES, s.ROLES
ASK, SEND, TOL = s.ASK, s.SEND, s.TOL
TRAIN_RATES = (.12, .45, .72, .94)
MODES = ("mandatory", "immediate", "fitted", "exact_public_credit")


def all_states(world, menu):
    truth = tuple(option in s.r.a.accepted(menu, world["requirements"][ROLES.index(role)])
                  for role,option in QUERY)
    for visible in product((False, True), repeat=len(QUERY)):
        yield tuple((1 if ok else -1) if show else 0
                    for show,ok in zip(visible,truth,strict=True)), truth


def dot(xs, weights):
    return sum(u*v for u,v in zip(xs,weights,strict=True))


def regress(rows):
    width = len(rows[0][0])
    normal = [[sum(x[i]*x[j] for x,_ in rows) + (1e-7 if i==j else 0.)
               for j in range(width)] + [sum(x[i]*y for x,y in rows)] for i in range(width)]
    for k in range(width):
        pivot = max(range(k,width),key=lambda row: abs(normal[row][k]))
        normal[k],normal[pivot] = normal[pivot],normal[k]
        scale=normal[k][k]
        assert abs(scale)>1e-12
        normal[k]=[v/scale for v in normal[k]]
        for i,row in enumerate(normal):
            if i!=k:
                normal[i]=[v-row[k]*p for v,p in zip(row,normal[k],strict=True)]
    return [row[-1] for row in normal]


def stage(menu, tree, rate, availability=(1.,1.), believed_availability=(1.,1.)):
    context, choose, _ = s.fixture(menu, tree, rate)
    local_queries = {role: tuple(i for i,q in enumerate(QUERY) if q[0]==role) for role in ROLES}

    @lru_cache(maxsize=None)
    def last(state, truth):
        query, _ = choose(state,1,"learned")
        decision, before, branches=context(state)
        if query is None:
            return before,float(decision!="UNRESOLVED"),0.,0.,0.
        branch=branches[query][truth[query]]
        available = availability[ROLES.index(QUERY[query][0])]
        send = available if rate*branch["record"]-SEND>TOL else 0.
        cost=ASK+SEND*send
        proofs=float(decision!="UNRESOLVED")+rate*branch["decision"]*send
        return before+rate*branch["record"]*send,proofs,cost,1.,float(send)

    @lru_cache(maxsize=None)
    def forecast(state, own, permitted, flavor):
        query,_=choose(state,1,"learned")
        if query is None:
            return 0.
        _,_,branches=context(state)
        offered=branches[query]
        if query in local_queries[own]:
            sign=QUERY[query][1] in permitted
            offered={sign:offered[sign] | {"probability":1.}}
        ready = believed_availability[ROLES.index(QUERY[query][0])]
        return ready*sum(b["probability"]*max(0.,rate*b[flavor]-SEND) for b in offered.values())-ASK

    def get(opening, truth):
        query,_=choose(opening,2,"learned")
        if query is None:
            return None
        role=QUERY[query][0]
        local=tuple(QUERY[i][1] for i in local_queries[role] if truth[i])
        _,_,branches=context(opening)
        branch=branches[query][truth[query]]
        updated=s.advance(opening,query,truth[query])
        learned_after=forecast(updated,role,local,"learned")
        learned_before=forecast(opening,role,local,"learned")
        public_after=forecast(updated,role,local,"record")
        public_before=forecast(opening,role,local,"record")
        # The local actor sees its own menu eligibility and public belief.
        # Labels below use the actual synthetic world only at training/evaluation.
        features=(1.,rate*branch["learned"],rate*(learned_after-learned_before))
        margin=rate*(branch["record"]+public_after-public_before)-SEND
        on=last(updated,truth)
        off=last(opening,truth)
        observed=rate*((on[0]-on[2])-(off[0]-off[2]))-SEND
        return {"query":QUERY[query],"x":features,"public_margin":margin,"label":observed,
                "instant":rate*branch["record"]-SEND,"sent":on,"withheld":off}

    def outcome(opening, item, mode, weights):
        decision,points,_=context(opening)
        if item is None:
            return {"record_gain":0.,"proof_gain":0.,"cost":0.,"questions":0.,
                    "sends":0.,"net":0.,"first_send":False,"first_query": None}
        margins={"mandatory":1.,"immediate":item["instant"],"fitted":dot(item["x"],weights),
                 "exact_public_credit":item["public_margin"]}
        send=margins[mode]>TOL
        p=rate*send
        expected=[p*a+(1-p)*b for a,b in zip(item["sent"],item["withheld"],strict=True)]
        record,proof,cost,queries,sends=expected
        record_gain=record-points
        cost+=ASK+SEND*send
        return {"record_gain":record_gain,"proof_gain":proof-float(decision!="UNRESOLVED"),"cost":cost,
                "questions":queries+1.,"sends":sends+send,"net":record_gain-cost,
                "first_send":send,"first_query":item["query"]}

    return get,outcome


def run():
    bench=s.r.BENCH
    config=E.read(bench/"case.json")
    tree=E.read(bench/"transfer-fit.json")["tree"]
    training=[]
    fit_worlds=s.r.fitted.typed_worlds()
    def synthetic_conditions(menu):
        return [{field:value} for field in menu[0] if field!="id"
                for value in sorted({row[field] for row in menu})]

    with patch.object(s.r.a, "conditions", synthetic_conditions):
        for world in fit_worlds:
            menu=world["menu"]
            for rate in TRAIN_RATES:
                get,_=stage(menu,tree,rate)
                for state,truth in all_states(world,menu):
                    item=get(state,truth)
                    if item:
                        training.append((item["x"],item["label"]))
    values=regress(training)
    results={}
    witnesses=E.read(HERE.parent/"sequential.json")["results"]["0.8"]["bridge_witnesses"]
    for rate in s.r.RATES:
        get,outcome=stage(config["menu"],tree,rate)
        all_scores={name:Counter() for name in MODES}
        handoffs={}
        for world in config["worlds"]:
            example=witnesses[world["id"]]
            opening_witness=tuple(
                next((1 if b.get("accepts") else -1 for b in example["opening"] if int(b["id"])==i),0)
                for i in range(len(QUERY))
            )
            for opening,truth in all_states(world,config["menu"]):
                item=get(opening,truth)
                scores={name:outcome(opening,item,name,values) for name in MODES}
                for name,row in scores.items():
                    all_scores[name].update({k:v for k,v in row.items()
                                             if k not in ("first_send","first_query")})
                    all_scores[name]["first_sends"]+=row["first_send"]
                    all_scores[name]["bridge_first_sends"]+=bool(item and row["first_send"]
                                                                and item["instant"]+SEND<TOL)
                if opening==opening_witness:
                    handoffs[world["id"]]={"branch":item,"outcomes":scores}
        results[str(rate)]={"totals":all_scores,"live_opening_witnesses":handoffs}
    files=(Path(__file__),HERE/"protocol.md",HERE.parent/"sequential.py",HERE.parent/"sequential.json",
           bench/"transfer-fit.json",bench/"case.json",s.r.a.public.signed.SIGNED/"roster.json")
    return {"training_rows":len(training),"training_worlds":len(fit_worlds),"training_rates":TRAIN_RATES,
            "weights":values,"training_mse":sum((dot(x,values)-y)**2 for x,y in training)/len(training),
            "results":results,"sha256":{p.name:sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__=="__main__":
    E.emit(run())
