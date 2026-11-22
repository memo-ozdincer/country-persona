"""Fit a selective comparison gate with at most two scored probe records."""
import argparse
from itertools import product
import json
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
FIT = RUNS/"native-reward-routing-fit"
DONOR = RUNS/"delisting-2744"
WRITERS = {
    "compact": RUNS/"delisting-witness-render/compact-results.json",
    "topic_guided": RUNS/"delisting-focused-writer/results.json",
    "generic": RUNS/"delisting-comparison-writer/results.json",
}
USE_FEE = .5
PROBE_FEE = 1.
HORIZONS = (1, 10, 100)


def read(path):
    return json.loads(path.read_text())


def plan():
    from hashlib import sha256

    paths = (Path(__file__),HERE/"protocol.md",FIT/"results.json",DONOR/"case.json",
             DONOR/"results.json",*WRITERS.values())
    old = read(FIT/"results.json")["evaluation"]["compact_ungated"]["rows"]
    donor = read(DONOR/"results.json")
    candidates = [name for name, row in donor["records"].items() if row["native"]]
    case = read(DONOR/"case.json")
    early, docs = list(case["early"]), list(case["late"])
    observation = [1 + int(donor["marks"][f"early/{key}"]["review"]>0) for key in early]
    reach = {}
    for key in candidates:
        e, d = key.split("/")
        i, j = early.index(e),docs.index(d)
        reach[key] = mean(
            row["prior"][i]*row["q_first"]*row["q_reply"]*row["arms"]["trained_content"]["send"][i]
            *int(row["arms"]["trained_content"]["reply"][observation[i]]==j) for row in old
        )
    assert len(candidates)==2
    return {"probe_order": sorted(candidates,key=lambda k:(-reach[k],k)),
            "reach": reach,"use_fee": USE_FEE,"probe_fee": PROBE_FEE,"horizons": list(HORIZONS),
            "inputs": {str(path.relative_to(RUNS)):sha256(path.read_bytes()).hexdigest() for path in paths}}


def probe(remaining, fetch, base, fee):
    """Prefer the known fallback until a scored probe beats it."""
    scores = {key:fetch(key) for key in remaining}
    return {"scores":scores,"licensed":[key for key,value in scores.items() if value-base[key]>fee]}


def run(spec):
    case = read(DONOR/"case.json")
    donor = read(DONOR/"results.json")
    rows = read(FIT/"results.json")["evaluation"]["compact_ungated"]["rows"]
    early, docs = list(case["early"]), list(case["late"])
    pairs = [f"{e}/{d}" for e,d in product(early,docs)]
    observed = [1+int(donor["marks"][f"early/{key}"]["review"]>0) for key in early]
    lead = sum(x["weight"] for x in case["public"])
    base = {f"{e}/{d}":lead+er["weight"]+dr["weight"]
            for (e,er),(d,dr) in product(case["early"].items(),case["late"].items())}
    first = [lead+row["weight"] for row in case["early"].values()]
    last = [lead+row["weight"] for row in case["late"].values()]
    fee = spec["use_fee"]
    score_banks = {name: {key:r["scores"]["ungated"] for key,r in read(path)["compiled"].items()}
                   for name,path in WRITERS.items()}
    prior = probe(spec["probe_order"],score_banks["compact"].__getitem__,base,fee)
    reports = {}
    for writer, bank in score_banks.items():
        learnt = {count: probe(spec["probe_order"][:count],bank.__getitem__,base,fee) for count in range(3)}
        traces = []
        for row in rows:
            q0,q1,cost,mass = (row[key] for key in ("q_first","q_reply","price","prior"))
            fixed = row["arms"]["trained_content"]

            def pay(reply, licensed, fit_values, sends=None):
                absent = (1-q1)*lead+q1*last[reply[0]]
                keys = [f"{e}/{docs[reply[obs]]}" for e,obs in zip(early,observed,strict=True)]
                if sends is None:
                    sends = []
                    for i,k in enumerate(keys):
                        estimate = fit_values[k]-fee if k in licensed else base[k]
                        sends.append(q0*((1-q1)*first[i]+q1*estimate-absent)>cost+1e-9)
                release, charge, write_cost, relations, failures = absent,0.,0.,0.,0.
                for i,k in enumerate(keys):
                    if not sends[i]:
                        continue
                    selected = bank[k] if k in licensed else base[k]
                    release += mass[i]*q0*((1-q1)*first[i]+q1*selected-absent)
                    charge += mass[i]*cost
                    if k in licensed:
                        routed = mass[i]*q0*q1
                        write_cost += fee*routed
                        relations += routed*int(selected==70)
                        failures += routed*int(selected==0)
                return {"utility":round(release-charge-write_cost,8),"released":round(release,8),
                        "send_cost":round(charge,8),"writer_fee":round(write_cost,8),"guard_failures":round(failures,8),
                        "relation_release":round(relations,8),"send":[int(x) for x in sends],"reply":list(reply)}

            def optimize(calibrated, arrivals_only=False):
                choices = [(a,b,b) for a,b in product(range(2),repeat=2)] if arrivals_only else product(range(2),repeat=3)
                return max((pay(reply,calibrated["licensed"],calibrated["scores"]) for reply in choices),
                           key=lambda value: value["utility"])

            policy = {"stale_frozen_team":pay(fixed["reply"],prior["licensed"],prior["scores"],fixed["send"]),
                      **{f"probe_{i}":optimize(cal) for i,cal in learnt.items()},
                      "frozen_team_probe_2":pay(fixed["reply"],learnt[2]["licensed"],learnt[2]["scores"],fixed["send"]),
                      "best_arrival_probe_2":optimize(learnt[2],arrivals_only=True)}
            # For the measured banks, granting the selector access to every
            # score cannot make a crossed pair worth the writing fee.
            complete = probe(pairs,bank.__getitem__,base,fee)
            oracle = optimize(complete)
            policy["complete_score_oracle"] = oracle
            assert policy["probe_2"]["utility"]==oracle["utility"]
            traces.append({"q_first":q0,"q_reply":q1,"price":cost,"prior":mass,"policies":policy})
        summary = {}
        for arm in traces[0]["policies"]:
            report = [item["policies"][arm] for item in traces]
            summary[arm] = {metric:round(mean(item[metric] for item in report),8) for metric in
                            ("utility","released","send_cost","writer_fee","guard_failures","relation_release")}
        for i in range(3):
            selected = summary[f"probe_{i}"]
            selected["utility_after_probe_cost"] = {
                str(n):round(selected["utility"]-i*spec["probe_fee"]/n,8) for n in spec["horizons"]
            }
        reports[writer] = {"observed_probes":learnt,"summary":summary,"held":traces}
    return {"prior":prior,"writers":reports}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--plan",action="store_true")
    args = p.parse_args()
    spec = plan()
    if not args.plan:
        assert spec==read(HERE/"plan.json")
    print(json.dumps(spec if args.plan else run(spec),indent=2))
