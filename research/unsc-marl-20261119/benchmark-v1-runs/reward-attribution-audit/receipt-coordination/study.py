"""Evaluate and fit receipt-conditioned policies against source-preserving records."""
import argparse
from hashlib import sha256
from itertools import permutations, product
import json
from math import exp, prod
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent.parent
BANKS = {
    "2475": RUNS / "disability-2475-transfer/bound-comparison/scored.json",
    "2686": RUNS / "tolerance-2686-transfer/scoped-writer/scores.json",
}
RATES = (.35,.55,.75,.95)
FEES = (1,3,5,8)
ORDERS = tuple(permutations(range(3)))
MASKS = range(8)
UPDATES = 120
LEARNING_RATE = .08
TOL = 1e-9


def read(path):
    return json.loads(path.read_text())


def pin(path):
    return sha256(path.read_bytes()).hexdigest()


def plan():
    return {"rates": list(RATES), "fees": list(FEES), "updates": UPDATES, "learning_rate": LEARNING_RATE,
            "sha256": {str(p.relative_to(RUNS)):pin(p) for p in (Path(__file__),HERE/"protocol.md",*BANKS.values())}}


def banks():
    first, second = (read(path)["banks"] for path in BANKS.values())
    return {"2475": first["authored/rule"], "2686": second["verbatim"],
            "2475_additive": first["authored/none"]}


def past_masks(order, turn):
    seen = sum(1 << x for x in order[:turn])
    return [mask for mask in MASKS if mask & seen == mask]


def send_flags(scores, rate, fee):
    return [rate*(scores[1 << i]-scores[0]) > fee for i in range(3)]


def scene(scores, order, rate, fee):
    features = {}
    prior = send_flags(scores, rate, fee)
    for turn, desk in enumerate(order):
        bit = 1 << desk
        standalone = scores[bit]-scores[0]
        future = order[turn+1:]
        for mask in past_masks(order, turn):
            current = scores[mask | bit]-scores[mask]
            expected = 0.
            for hits in product((0,1), repeat=len(future)):
                mass = prod(rate*prior[i] if hit else 1-rate*prior[i]
                            for i, hit in zip(future, hits, strict=True))
                extra = sum(1 << i for i, hit in zip(future, hits, strict=True) if hit)
                expected += mass*(scores[mask|extra|bit]-scores[mask|extra])
            features[turn,mask] = (
                (rate*standalone-fee)/7,
                (1., (rate*standalone-fee)/7, rate*(current-standalone)/7, rate*(expected-current)/7),
            )
    return scores, order, rate, fee, features


def logits(features, weights):
    return {key: baseline+sum(w*x for w,x in zip(weights,f,strict=True))
            for key,(baseline,f) in features.items()}


def replay(problem, policy, gradient=None):
    scores, order, rate, fee, features = problem

    def step(turn, mask):
        if turn == len(order):
            return scores[mask], [0.]*4
        bit = 1 << order[turn]
        no, no_grad = step(turn+1, mask)
        yes, yes_grad = step(turn+1, mask|bit)
        p = policy[turn,mask]
        noisy_delta = rate*(yes-no)-fee
        if gradient is None:
            slope = [0.]*4
        else:
            slope = [(1-p*rate)*a + p*rate*b + p*(1-p)*noisy_delta*x
                     for a,b,x in zip(no_grad, yes_grad, features[turn,mask][1], strict=True)]
        return no + p*noisy_delta, slope

    return step(0,0)


def exact(problem):
    scores, order, rate, fee, features = problem
    optimum = {mask: score for mask,score in enumerate(scores)}
    policy = {}
    for turn in reversed(range(len(order))):
        bit = 1 << order[turn]
        for mask in past_masks(order,turn):
            difference = rate*(optimum[mask|bit]-optimum[mask])-fee
            policy[turn,mask] = int(difference > TOL)
            optimum[mask] += max(0., difference)
    static = max(replay(problem, {key:a[key[0]] for key in features})[0]
                 for a in product((0,1), repeat=3))
    assert abs(replay(problem, policy)[0]-optimum[0]) <= TOL
    return optimum[0], static


def fit(panel):
    weights = [0.]*4
    trace = {}
    for i in range(UPDATES+1):
        outcomes = []
        for problem in panel:
            probs = {key:1/(1+exp(-z)) for key,z in logits(problem[4],weights).items()}
            outcomes.append(replay(problem, probs, gradient=True))
        if i in (0,30,60,120):
            trace[str(i)] = {"weights": weights.copy(), "training_stochastic_net": mean(r[0] for r in outcomes)}
        if i != UPDATES:
            weights = [w+LEARNING_RATE*mean(result[1][j] for result in outcomes) for j,w in enumerate(weights)]
    return weights, trace


def panels(values):
    return [scene(values,order,rate,fee) for order,rate,fee in product(ORDERS,RATES,FEES)]


def evaluate(panel, weights, exhaustive):
    rows = []
    for problem in panel:
        _, order, rate, fee, features = problem
        policies = {
            "standalone": {key:int(z > TOL) for key,(z,_) in features.items()},
            "observed_marginal": {key:int(z+f[2] > TOL) for key,(z,f) in features.items()},
            "future_forecast": {key:int(z+f[2]+f[3] > TOL) for key,(z,f) in features.items()},
            "fit": {key:int(z > TOL) for key,z in logits(features,weights).items()},
            "fit_without_receipts": {key:int(z > TOL) for key,z in logits(
                {key:features[key[0],0] for key in features},weights).items()},
        }
        values = {name:replay(problem,p)[0] for name,p in policies.items()}
        adaptive, static = exact(problem)
        if exhaustive:
            # Independently check every seven-decision policy by forward propagation.
            def forward(bits):
                p = dict(zip(features,bits,strict=True))
                mass, cost = {0:1.}, 0.
                for turn,desk in enumerate(order):
                    next_mass = {mask:0. for mask in past_masks(order,turn+1)}
                    for mask,prob in mass.items():
                        reward = p[turn,mask]
                        cost += prob*reward*fee
                        next_mass[mask] += prob*(1-reward*rate)
                        next_mass[mask | (1 << desk)] += prob*reward*rate
                    mass = next_mass
                return sum(problem[0][mask]*prob for mask,prob in mass.items())-cost
            assert abs(max(forward(a) for a in product((0,1),repeat=len(features)))-adaptive) <= TOL
        assert max(values.values()) <= adaptive+TOL
        assert values["fit_without_receipts"] <= static+TOL
        values.update(adaptive_ceiling=adaptive,static_ceiling=static)
        rows.append({"order":list(order),"delivery":rate,"send_fee":fee,"net":values,
                     "observations": [list(key) for key in features],
                     "actions":{name:list(policy.values()) for name,policy in policies.items()}})
    return {"mean":{name:mean(row["net"][name] for row in rows) for name in rows[0]["net"]},
            "adaptive_ceiling_wins":sum(row["net"]["adaptive_ceiling"] > row["net"]["static_ceiling"]+TOL for row in rows),
            "rows":rows}


def run():
    lock = HERE/"plan.json"
    assert read(lock) == plan()
    values = banks()
    cases = {name:panels(bank) for name,bank in values.items()}
    learned = {name:fit(cases[name]) for name in ("2475","2686")}
    outputs = {name:evaluate(cases[name],learned[other][0],name != "2475_additive")
               for name,other in (("2475","2686"),("2686","2475"),("2475_additive","2686"))}
    assert outputs["2475_additive"]["adaptive_ceiling_wins"] == 0
    return {"plan_sha256":pin(lock),"training":{name:trace for name,(_,trace) in learned.items()},
            "held":outputs}


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("plan","run"))
    print(json.dumps({"plan":plan,"run":run}[parser.parse_args().mode](),indent=2))
