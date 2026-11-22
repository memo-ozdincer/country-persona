"""Fit cooperative routing on stored, reviewed native-writer terminal outcomes."""
import argparse
from itertools import product
import json
from pathlib import Path
from statistics import mean
import runpy
import sys
from types import SimpleNamespace

import numpy as np

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
SOURCE = RUNS / "sender-value-family-transfer"
sys.path.insert(0, str(SOURCE))
study = SimpleNamespace(**runpy.run_path(str(SOURCE/"study.py")))

team = study.team
read = study.read
writer = RUNS / "delisting-witness-render" / "compact-results.json"
topic = RUNS / "delisting-focused-writer" / "results.json"
prior = RUNS / "delisting-2744" / "results.json"
CHECKPOINTS = (1, 32, 128, 256, team.UPDATES)


def plan():
    inputs = (Path(__file__), HERE/"protocol.md", SOURCE/"study.py", SOURCE/"plan.json",
              writer, topic, prior, Path(team.__file__))
    return {
        "train": {"seed": team.SEED, "batch": team.BATCH, "updates": team.UPDATES,
                  "prices": list(team.TRAIN_PRICES), "delivery": list(team.TRAIN_DELIVERY),
                  "queries_per_episode": 2},
        "held": {"prices": list(team.TEST_PRICES), "delivery": list(team.TEST_DELIVERY),
                 "priors": [list(p) for p in team.TEST_PRIORS]},
        "sha256": {str(path.relative_to(RUNS)): study.transfer.digest(path) for path in inputs},
    }


def environment():
    case = study.case_banks()[0]["2744"]
    views = [row["view"] for row in case["views"]]
    data = {
        "public": float(case["public"]),
        "first": np.array([r["first_only"] for r in case["views"]]),
        "last": case["public"] + np.array(case["doc_values"]),
        "observed": np.array([r["observation"] for r in case["views"]]),
        "views": views, "docs": case["docs"],
    }
    def table(path, field):
        bank = read(path)["compiled"]
        return np.array([[bank[f"{view}/{doc}"]["scores"][field] for doc in case["docs"]] for view in views])
    return data, {
        "compact_ungated": table(writer, "ungated"),
        "compact_admitted": table(writer, "admitted"),
        "topic_guided_admitted": table(topic, "admitted"),
        "typed": np.array([row["joined"] for row in case["views"]]),
    }


def train(data, joined, content, spec):
    options = spec["train"]
    rng = np.random.default_rng(options["seed"])
    n = options["batch"]
    obs = data["observed"] if content else np.ones_like(data["observed"])
    counts = np.zeros((3,2))
    totals = np.zeros_like(counts)
    receiver = np.zeros(3)
    m, v = np.zeros(3), np.zeros(3)
    mean_utility = data["public"]
    history = []

    def weights():
        return study.fit.learner.sender_weights(counts[None,:,:], totals[None,:,:])[0]

    for step in range(1,options["updates"]+1):
        view = rng.integers(3,size=n)
        q0 = rng.choice(options["delivery"],size=n)
        q1 = rng.choice(options["delivery"],size=n)
        price = rng.choice(options["prices"],size=n)
        send = rng.random(n) < team.sigmoid((weights()[view]*team.features(q0,q1,price)).sum(axis=1))
        delivery = rng.random(n)<q0
        reply_draw = rng.random(n)
        returned = rng.random(n)<q1
        without_obs = np.zeros(n,dtype=int)
        with_obs = np.where(delivery,obs[view],0)
        p0, p1 = team.sigmoid(receiver[without_obs]), team.sigmoid(receiver[with_obs])
        a0, a1 = (reply_draw<p0).astype(int), (reply_draw<p1).astype(int)
        withheld = np.where(returned,data["last"][a0],data["public"])
        forwarded = np.where(delivery,np.where(returned,joined[view,a1],data["first"][view]),withheld)
        np.add.at(counts,(view[delivery],returned[delivery].astype(int)),1)
        np.add.at(totals,(view[delivery],returned[delivery].astype(int)),(forwarded-withheld)[delivery])
        reward = np.where(send,forwarded-price,withheld)
        state = np.where(send,with_obs,0)
        probability = np.where(send,p1,p0)
        action = np.where(send,a1,a0)
        grad = np.zeros(3)
        np.add.at(grad,state,(reward-mean_utility)*(action-probability)/(10*n))
        receiver,m,v = team.adam(receiver,grad,m,v,step)
        mean_utility = .95*mean_utility + .05*float(np.mean(reward))
        if step in CHECKPOINTS:
            history.append({"step": step, "counts": counts.astype(int).tolist(),
                            "sums": totals.tolist(), "reply": receiver.tolist(),
                            "sender": weights().tolist(), "mean_batch_utility": float(np.mean(reward))})
    return history


def evaluate(data, joined, histories, spec):
    old = read(prior)
    donor = old["history"][-1]
    old_s = np.array(donor["sender"][1])
    old_r = (np.array(donor["receiver"][1])>0).astype(int)
    new_s = np.array(histories["content"][-1]["sender"])
    new_r = (np.array(histories["content"][-1]["reply"])>0).astype(int)
    arrival_s = np.array(histories["arrival"][-1]["sender"])
    arrival_r = (np.array(histories["arrival"][-1]["reply"])>0).astype(int)[[0,1,1]]
    # Known criterion weights give the typed model a strong routing control.
    _, typed = environment()
    typed = typed["typed"]
    held = spec["held"]
    all_rows = []
    choice = np.arange(3)
    for q0,q1,price,prior_mass in product(held["delivery"],held["delivery"],held["prices"],held["priors"]):
        features = team.features(q0,q1,price)
        mass = np.array(prior_mass)

        def pay(reply, sends=None, training_table=None):
            actions = np.asarray(reply)[data["observed"]]
            absent = (1-q1)*data["public"] + q1*data["last"][reply[0]]
            chosen = joined[choice,actions]
            delta = q0*((1-q1)*data["first"] + q1*chosen - absent)
            if sends is None:
                model = joined if training_table is None else training_table
                sends = q0*((1-q1)*data["first"] + q1*model[choice,actions] - absent) > price+1e-9
            release = absent + mass @ (sends*delta)
            charge = price*(mass @ sends)
            observed_mass = mass*sends*q0*q1
            relation = observed_mass @ (chosen==70)
            blocked = observed_mass @ (chosen==0)
            return {"utility": round(float(release-charge),8), "release": round(float(release),8),
                    "cost": round(float(charge),8), "relation": round(float(relation),8),
                    "guard_failure": round(float(blocked),8), "send": sends.astype(int).tolist(),
                    "reply": [int(x) for x in reply]}

        policies = {
            "trained_content": pay(new_r,new_s@features>0),
            "trained_arrival": pay(arrival_r,arrival_s@features>0),
            "prior_typed_fit": pay(old_r,old_s@features>0),
            "full_rubric_rule": pay(old_r,training_table=typed),
            "new_sender_old_reply": pay(old_r,new_s@features>0),
            "old_sender_new_reply": pay(new_r,old_s@features>0),
            "best_arrival": max((pay((a,b,b)) for a,b in product(range(2),repeat=2)),
                                key=lambda row: row["utility"]),
            "oracle": max((pay(r) for r in product(range(2),repeat=3)),key=lambda row: row["utility"]),
        }
        assert max(row["utility"] for row in policies.values()) <= policies["oracle"]["utility"]+1e-8
        all_rows.append({"q_first": q0,"q_reply": q1,"price": price,"prior": prior_mass, "arms": policies})
    assert len(all_rows)==96
    scores = [r["arms"] for r in all_rows]
    summary = {key: {
        **{metric: round(mean(row[key][metric] for row in scores),8)
           for metric in ("utility","release","cost","relation","guard_failure")},
        "oracle_matches": sum(row[key]["utility"]==row["oracle"]["utility"] for row in scores),
        "wins_over_best_arrival": sum(row[key]["utility"]>row["best_arrival"]["utility"] for row in scores)
    } for key in scores[0]}
    return {"summary": summary, "rows": all_rows}


def run(spec):
    data,banks = environment()
    histories = {name: train(data,banks["compact_ungated"],name=="content",spec)
                 for name in ("content","arrival")}
    records = {name: evaluate(data,bank,histories,spec) for name,bank in banks.items()}
    expected = read(writer)["policy"]["ungated"]["summary"]
    for new, old in (("prior_typed_fit","native_fit"),("oracle","oracle"),("best_arrival","best_arrival_only")):
        assert records["compact_ungated"]["summary"][new]["utility"]==expected[old]
    return {"training": histories,
            "queries_per_arm": spec["train"]["batch"]*spec["train"]["updates"]*spec["train"]["queries_per_episode"],
            "tested_banks": {k: v.tolist() for k,v in banks.items()}, "evaluation": records}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    spec = plan()
    if not args.plan:
        assert spec==read(HERE/"plan.json")
    print(json.dumps(spec if args.plan else run(spec),indent=2))
