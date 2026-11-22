"""Train a shared send/silence head from archived writer reward intervals."""
import argparse
from itertools import product
import json
from math import exp
from pathlib import Path
from statistics import mean
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import audit

RATES = (.35, .55, .75, .95)
FEES = (1, 3, 5, 8)
UPDATES = 120
STEP = .08
MASKS = range(8)
DESKS = range(3)
TOL = 1e-10


def plan():
    paths = (Path(__file__), HERE / "protocol.md", Path(audit.__file__),
             audit.HERE / "plan.json", audit.HERE / "results.json")
    return {"rates": list(RATES), "fees": list(FEES), "updates": UPDATES, "step": STEP,
            "pins": {str(p.relative_to(audit.RUNS)): audit.sha(p) for p in paths}}


def load():
    d = audit.read(audit.FILES["disability"])
    disability = {name: audit.load_bank(d, d["banks"][f"authored/{name}"], f"authored/{name}/")
                  for name in ("none", "plain", "scope")}
    t = audit.read(audit.FILES["tolerance_scoped"])
    tolerance = {name: audit.load_bank(t, t["banks"][name], f"{name}/")
                 for name in ("scoped", "verbatim")}
    for name in ("original", "revised"):
        bank = audit.read(audit.FILES[f"tolerance_{name}"])
        tolerance[name] = audit.load_bank(bank, bank["score_bank"])
    return {"2475": (disability, "none", "none"), "2686": (tolerance, "original", "verbatim")}


def with_masses(probability):
    return [prod([r if mask & (1 << i) else 1-r for i, r in enumerate(probability)])
            for mask in MASKS]


def prod(values):
    result = 1.
    for v in values:
        result *= v
    return result


def sigmoid(x):
    return 1. / (1. + exp(-x))


def scenes(case):
    _, _, available = case
    banks = case[0]
    proxy = [banks[available][1 << i].nominal - banks[available][0].nominal for i in DESKS]
    for rate, fee in product(RATES, FEES):
        yield rate, fee, proxy, [(1., value/7, rate) for value in proxy]


def policy(scene, weights):
    rate, fee, proxy, x = scene
    return [sigmoid((rate * value-fee)/7 + sum(w*j for w,j in zip(weights, row, strict=True)))
            for value, row in zip(proxy, x, strict=True)]


def paired(scene, probabilities, banks):
    rate, fee, _, _ = scene
    results = []
    for i in DESKS:
        received = with_masses([rate * p if i != j else 0. for j,p in enumerate(probabilities)])
        signed = {mask: received[mask & ~(1 << i)] * rate * (1 if mask & (1 << i) else -1)
                  for mask in MASKS}
        assert abs(sum(signed.values())) < TOL
        results.append({name: audit.contrast(signed, grades) for name, grades in banks.items()})
    for row in results:
        for result in row.values():
            result["nominal"] -= fee
            result["band"] = [value-fee for value in result["band"]]
    return results


def value(scene, probabilities, records):
    rate, fee, _, _ = scene
    probs = with_masses([rate*p for p in probabilities])
    return sum(probs[mask]*records[mask].nominal for mask in MASKS) - fee*sum(probabilities)


def gradient(scene, weights, case, mode):
    banks, nominal, _ = case
    probabilities = policy(scene, weights)
    grade = paired(scene, probabilities, banks)
    update = [0.] * 3
    coverage = 0
    for p, features, rewards in zip(probabilities, scene[3], grade, strict=True):
        lo, hi = audit.across(rewards)["band"]
        effect = rewards[nominal]["nominal"] if mode == "nominal" else lo if lo > 0 else hi if hi < 0 else 0.
        coverage += abs(effect) > TOL
        for k,x in enumerate(features):
            update[k] += effect*p*(1-p)*x
    return update, coverage


def train(case, mode):
    weights = [0.] * 3
    training = list(scenes(case))
    trace = {}
    for step in range(UPDATES+1):
        grads = [gradient(scene, weights, case, mode) for scene in training]
        if step in (0,30,60,120):
            trace[str(step)] = {"weights": weights.copy(), "nonzero_actor_terms": sum(n for _,n in grads),
                                "nominal_stochastic_net": mean(value(scene, policy(scene, weights), case[0][case[1]])
                                                               for scene in training)}
        if step != UPDATES:
            weights = [w + STEP*mean(g[k] for g,_ in grads) for k,w in enumerate(weights)]
    return weights, trace


def replay(scene, actions, records):
    # Independent joint branch calculation over actual send and delivery masks.
    rate, fee, _, _ = scene
    sent = sum(1 << i for i, bit in enumerate(actions) if bit)
    return sum(rate ** mask.bit_count() * (1-rate)**((sent ^ mask).bit_count()) * records[mask].nominal
               for mask in MASKS if (mask & sent) == mask) - fee*sent.bit_count()


def evaluate(case, arms):
    rows = []
    for scene in scenes(case):
        plans = {key: [int(p > .5) for p in policy(scene, w)] for key,w in arms.items()}
        result = {}
        for name, records in case[0].items():
            values = {key: value(scene, acts, records) for key,acts in plans.items()}
            ceiling = max(replay(scene, acts, records) for acts in product((0,1), repeat=3))
            assert max(values.values()) <= ceiling+TOL
            assert all(abs(values[key]-replay(scene, acts, records)) <= TOL for key,acts in plans.items())
            result[name] = values | {"ceiling": ceiling}
        rows.append({"rate":scene[0], "fee":scene[1], "sends":plans, "net":result})
    result = {}
    for writer in case[0]:
        result[writer] = {}
        for arm in arms.keys() | {"ceiling"}:
            gains = [x["net"][writer][arm]-x["net"][writer]["fixed"] for x in rows]
            result[writer][arm] = {"net": mean(x["net"][writer][arm] for x in rows),
                                   "wins_vs_fixed":sum(v > TOL for v in gains),
                                   "losses_vs_fixed":sum(v < -TOL for v in gains)}
    # Keep the output order independent of set hashing.
    return {"summary": {key:dict(sorted(value.items())) for key,value in result.items()}, "rows":rows}


def check_gradient(case):
    rates = list(scenes(case))
    scene = rates[7]
    weights = [0.13,-0.19,0.09]
    measured, _ = gradient(scene, weights, case, "nominal")
    records = case[0][case[1]]
    eps = 1e-5
    for k in DESKS:
        plus, minus = weights.copy(), weights.copy()
        plus[k] += eps
        minus[k] -= eps
        numerical = (value(scene, policy(scene, plus), records) - value(scene, policy(scene, minus), records))/(2*eps)
        assert abs(numerical-measured[k]) < 1e-7


def run():
    lock = HERE / "plan.json"
    assert audit.read(lock) == plan()
    cases = load()
    folds = {}
    for training, held in (("2475","2686"), ("2686","2475")):
        case = cases[training]
        check_gradient(case)
        arms = {"fixed":[0.]*3}
        traces = {}
        for mode in ("nominal", "agreement"):
            arms[mode], traces[mode] = train(case, mode)
        folds[f"{training}_to_{held}"] = {"train":traces, "held":evaluate(cases[held], arms)}
    return {"plan_sha256":audit.sha(lock), "folds":folds}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run"))
    print(json.dumps({"plan": plan, "run": run}[parser.parse_args().mode](), indent=2))
