"""Learn when an optional native reread improves an archived joint record."""
import argparse
from hashlib import sha256
from itertools import product
import json
from math import exp
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
FEES = (.5,2.,4.,8.)
ORDERS = ("ab","ba")
STEPS = 160
STEP_SIZE = .12
TOL = 1e-10


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return sha256(path.read_bytes()).hexdigest()


def plan():
    paths = (Path(__file__), HERE/"protocol.md", PARENT/"scores.json",
             PARENT/"lexical-contrast/scores.json", PARENT.parent/"results.json")
    return {"fees":list(FEES), "steps":STEPS, "step_size":STEP_SIZE,
            "sha256":{str(p.relative_to(PARENT)):sha(p) for p in paths[:-1]} |
                     {"case-results":sha(paths[-1])}}


def samples():
    original = read(PARENT/"scores.json")["modes"]
    practice, held = {}, {}
    for mode,b in original.items():
        for truth,row in b["decisions"].items():
            practice[mode,int(truth)] = {
                order:(row[order]["margin_0_minus_1"],row[order]["raw_mapped"],b["deployed"][truth])
                for order in ORDERS}
    for mode,b in read(PARENT/"lexical-contrast/scores.json").items():
        for truth,row in b["observations"].items():
            held[mode,int(truth)] = {r["order"]:(r["margin"],r["raw"],int(row["mean_margin"] < 0))
                                     for r in row["orders"]}
    return practice,held


def features(order, margin, rate, fee):
    return (1., abs(margin)/3, margin/3, float(order=="ba"), rate, fee/4)


def logit(w, x):
    return sum(a*b for a,b in zip(w,x,strict=True))


def effect(bank, truth, choice, revise, q):
    # A read is considered only after the first card has arrived.
    lost = bank[f"{truth}/None"]["grade"]["released_70"]
    keep = (1-q)*lost+q*bank[f"{truth}/{choice}"]["grade"]["released_70"]
    new = (1-q)*lost+q*bank[f"{truth}/{revise}"]["grade"]["released_70"]
    return new-keep


def fit(practice, bank, contexts):
    w = [0.] * 6
    trace = {}
    rows = []
    for (q,p),fee,((mode,truth),choices),order in product(contexts,FEES,practice.items(),ORDERS):
        margin,raw,revised = choices[order]
        mass = q*(p if truth==0 else 1-p)
        gain = effect(bank,truth,raw,revised,q)-fee
        rows.append((features(order,margin,q,fee),mass,gain))
    for i in range(STEPS+1):
        probabilities = [1/(1+exp(-logit(w,x))) for x,_,_ in rows]
        if i in (0,40,80,160):
            trace[str(i)] = {"weights":w.copy(),
                            "expected_net_gain_vs_one_call":mean(
                                prob*mass*gain for (x,mass,gain),prob in zip(rows,probabilities,strict=True))}
        if i != STEPS:
            grad = [mean(prob*(1-prob)*mass*gain*x[k]
                         for (x,mass,gain),prob in zip(rows,probabilities,strict=True))
                    for k in range(len(w))]
            w = [a+STEP_SIZE*b for a,b in zip(w,grad,strict=True)]
    return w,trace


def margin_threshold(practice,bank,q,fee):
    rows = [(abs(m),effect(bank,truth,raw,revised,q)-fee)
            for (_,truth), choices in practice.items() for m,raw,revised in choices.values()]
    candidates = [-1., *sorted({m for m,_ in rows})]
    return max(candidates,key=lambda t:(sum(delta for m,delta in rows if m<=t),-t))


def order_table(practice,bank,q,fee):
    return {order:mean(effect(bank,truth,*choices[order][1:],q) for (_,truth),choices in practice.items())>fee
            for order in ORDERS}


def test_row(rows, bank, q, prior, fee, w, threshold, table, absent, distribution):
    outcome = {}
    for arm in ("never","always","fit","threshold","order_table","hindsight","canonical"):
        released, reads = 0.,0.
        for truth,early,late,order in product((0,1),(0,1),(0,1),distribution):
            m,raw,revised = rows[truth][order]
            net_effect = effect(bank,truth,raw,revised,q)-fee
            read_again = {
                "never":False,"always":True,"fit":logit(w,features(order,m,q,fee))>0,
                "threshold":abs(m)<=threshold,"order_table":table[order],"hindsight":net_effect>0,
                "canonical":False,
            }[arm] and early
            action = absent if not early else rows[truth]["ab"][1] if arm=="canonical" else revised if read_again else raw
            earlier = truth if early else None
            answer = action if late else None
            mass = (prior if truth==0 else 1-prior)*(q if early else 1-q)*(q if late else 1-q)/len(distribution)
            released += bank[f"{earlier}/{answer}"]["grade"]["released_70"]*mass
            reads += read_again*mass
        outcome[arm] = {"released":released,"extra_calls":reads,"net":released-reads*fee}
    for arm in set(outcome)-{"canonical"}:
        assert outcome[arm]["net"] <= outcome["hindsight"]["net"]+TOL
    assert abs(outcome["always"]["extra_calls"]-q) < TOL
    return outcome


def run():
    lock = HERE/"plan.json"
    assert read(lock) == plan()
    archive = read(PARENT.parent/"results.json")
    bank = archive["valid_receipt_records"]
    contexts = [(r["receipt_probability"],r["first_card_0_probability"]) for r in archive["conditions"]]
    practice, held = samples()
    assert set(practice).isdisjoint(held)
    w,trace = fit(practice,bank,contexts)
    absent = read(PARENT/"scores.json")["absent"]["action"]
    result = []
    for mode,(q,p),fee,dist in product(sorted({mode for mode,_ in held}),contexts,FEES,(ORDERS,("ab",),("ba",))):
        threshold = margin_threshold(practice,bank,q,fee)
        table = order_table(practice,bank,q,fee)
        row = test_row([held[mode,i] for i in (0,1)],bank,q,p,fee,w,threshold,table,absent,dist)
        result.append({"mode":mode,"rate":q,"prior":p,"fee":fee,"first_orders":list(dist),
                       "threshold":threshold,"order_table":table,"arms":row})
    summary = {}
    for dist in (ORDERS,("ab",),("ba",)):
        rows = [x["arms"] for x in result if tuple(x["first_orders"])==dist]
        summary["/".join(dist)] = {key:{metric:mean(row[key][metric] for row in rows)
                                      for metric in rows[0][key]} for key in rows[0]}
    return {"plan_sha256":sha(lock), "trace":trace,"held_summary":summary,"held_rows":result}


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("run","plan"))
    print(json.dumps({"run":run,"plan":plan}[parser.parse_args().mode](),indent=2))
