"""Leave one docket out when learning paired delivery values."""
import argparse
import json
from itertools import product
from pathlib import Path
from statistics import mean
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
BRIDGE = RUNS / "delisting-to-reporting-transfer"
PREVIOUS = RUNS / "decomposed-source-gate"
sys.path.insert(0, str(BRIDGE))
import transfer

fit = transfer.fit
team = fit.team
read = fit.read
GRIDS = {"original": (8, 11, 15), "lower": (1, 3, 5)}
FAMILIES = ("2664", "2739", "2744")


def plan():
    paths = (Path(__file__), HERE/"protocol.md", BRIDGE/"plan.json", BRIDGE/"results.json",
             BRIDGE/"wording/results.json", PREVIOUS/"results.json",
             transfer.TARGET/"plan.json", transfer.TARGET/"verified.json", transfer.TARGET/"fit.py",
             transfer.DONOR/"case.json", transfer.DONOR/"results.json", Path(team.__file__))
    return {"families": list(FAMILIES), "grids": {key: list(value) for key, value in GRIDS.items()},
            "label_assignment": "frozen role-scoped verifier",
            "training_pairings": ["opening received", "opening absent"],
            "folds": {family: [peer for peer in FAMILIES if peer != family] for family in FAMILIES},
            "pins": {str(path.relative_to(RUNS)): transfer.digest(path) for path in paths}}


def compile_family(key, public, views, docs, own_values, doc_values, early_types, doc_types,
                   relation_bonus, observations, scores, reply):
    rows = []
    for view, own, early_type, observation in zip(views, own_values, early_types, observations, strict=True):
        action = reply[observation]
        eligible = early_type is not None and early_type == doc_types[action]
        doc_delta = doc_values[action] - doc_values[reply[0]]
        rows.append({"view": view, "own": own, "observation": observation, "reply": docs[action],
                     "doc_delta": doc_delta, "eligible": eligible, "bonus": relation_bonus,
                     "first_only": public + own, "joined": [scores[view, doc] for doc in docs]})
    return {"family": key, "public": public, "views": rows,
            "docs": docs, "doc_values": doc_values, "fixed_reply": reply}


def case_banks():
    bridge = read(transfer.TARGET/"plan.json")["cases"]
    outputs = read(transfer.TARGET/"verified.json")["outputs"]
    _, comparison, _, records = fit.bank(bridge, outputs)
    public, opening, replies, _, observed = comparison
    cases = {}
    for i, (key, case) in enumerate(bridge.items()):
        views, docs = map(list, (case["early"], case["late"]))
        weight = next(row["weight"] for row in case["rubric"] if row["id"] == case["relation"])
        table = {(v,d): records[f"{key}/{v}/{d}"]["audited_score"] for v,d in product(views,docs)}
        obs = observed[i].tolist()
        early_types = ["follow-up" if signal == 2 else None for signal in obs]
        cases[key] = compile_family(key, int(public[i]), views, docs, (opening[i]-public[i]).tolist(),
                                    (replies[i]-public[i]).tolist(), early_types, [None, "follow-up"],
                                    weight, obs, table, [0,0,1])
    donor_case = read(transfer.DONOR/"case.json")
    donor = read(transfer.DONOR/"results.json")
    views, docs = list(donor_case["early"]), list(donor_case["late"])
    votes = [donor["marks"][f"early/{view}"] for view in views]
    candidates = [next((key for key, value in values.items() if value > 0), None) for values in votes]
    assert all(sum(value > 0 for value in values.values()) <= 1 for values in votes)
    bonuses = {v["weight"] for v in donor_case["relations"].values()}
    assert len(bonuses) == 1
    cases["2744"] = compile_family(
        "2744", sum(row["weight"] for row in donor_case["public"]), views, docs,
        [row["weight"] for row in donor_case["early"].values()],
        [row["weight"] for row in donor_case["late"].values()], candidates, docs,
        bonuses.pop(), [1 + int(row["review"] > 0) for row in votes],
        {(v,d): donor["records"][f"{v}/{d}"]["audited"] for v,d in product(views,docs)}, [0,1,0]
    )
    target = bridge["2739"]
    stress = {}
    wording = read(BRIDGE/"wording/results.json")
    split = read(PREVIOUS/"results.json")
    for name, report, classes in (
        ("averaged_paraphrase", wording["variants"]["paraphrases"], [2,2,1]),
        ("split_paraphrase", split["target"]["variants"]["paraphrases"], [2,1,1])
    ):
        case = cases["2739"]
        views, docs = list(target["early"]), case["docs"]
        scores = {(v,d): report["released_pairs"][f"2739/{v}/{d}"] for v,d in product(views,docs)}
        stress[name] = compile_family("2739", case["public"], views, docs, [r["own"] for r in case["views"]],
                                      case["doc_values"], ["follow-up" if c == 2 else None for c in classes],
                                      [None,"follow-up"], 14, classes, scores, case["fixed_reply"])
    return cases, stress


def train(cases, source_families):
    log = []
    raw = {str(i): [[], []] for i in (0,1)}
    fractions = []
    for key in source_families:
        data = cases[key]
        no_opening = data["public"] + data["doc_values"][data["fixed_reply"][0]]
        for row in data["views"]:
            action = data["fixed_reply"][row["observation"]]
            is_compatible = str(int(row["eligible"]))
            for returned in (0,1):
                absent = no_opening if returned else data["public"]
                present = row["joined"][action] if returned else row["first_only"]
                gain = present-absent
                known = row["own"] + returned*row["doc_delta"]
                residual = (gain-known)/row["bonus"] if row["eligible"] and returned else None
                if residual is not None:
                    fractions.append(residual)
                raw[is_compatible][returned].append(gain)
                log.append({"family": key, "view": row["view"], "return_delivery": returned,
                            "with_opening": present, "without_opening": absent,
                            "known_difference": known, "learnable_bonus_fraction": residual})
    assert len(log) == 12
    return {"source_families": source_families, "terminal_queries": 2*len(log), "paired_log": log,
            "raw": {key: [mean(samples) if samples else 0 for samples in values] for key,values in raw.items()},
            "relation_fraction": mean(fractions) if fractions else 0}


def evaluate(case, calibration):
    result = []
    fixed = case["fixed_reply"]
    public, doc = case["public"], case["doc_values"]
    first = np.array([v["first_only"] for v in case["views"]])
    joined = np.array([v["joined"] for v in case["views"]])
    obs = np.array([v["observation"] for v in case["views"]])
    own = np.array([v["own"] for v in case["views"]])
    doc_delta = np.array([v["doc_delta"] for v in case["views"]])
    bonus = np.array([v["bonus"]*v["eligible"] for v in case["views"]])
    raw = np.array([calibration["raw"][str(int(v["eligible"]))] for v in case["views"]])
    for group, prices in GRIDS.items():
        for q0,q1,price,prior in product(team.TEST_DELIVERY,team.TEST_DELIVERY,prices,team.TEST_PRIORS):
            mass = np.array(prior)
            def pay(reply, send=None):
                absent = public + q1*doc[reply[0]]
                arrived = (1-q1)*first + q1*joined[np.arange(3), np.asarray(reply)[obs]]
                gross = q0*(arrived-absent)
                if send is None:
                    send = gross > price
                release = float(absent + mass @ (gross*send))
                cost = float(price*(mass @ send))
                return {"release": round(release,8), "cost": round(cost,8),
                        "utility": round(release-cost,8), "send": [int(x) for x in send]}
            release_no_bonus = own + q1*doc_delta
            predicted = {
                "raw_transfer": raw @ [1-q1,q1],
                "factored_transfer": release_no_bonus + q1*bonus*calibration["relation_fraction"],
                "full_rubric_rule": release_no_bonus + q1*bonus,
                "no_bonus_rule": release_no_bonus,
            }
            arms = {name: pay(fixed,q0*gains > price+1e-9) for name,gains in predicted.items()}
            arms["best_sender"] = pay(fixed)
            arms["arrival_only"] = max((pay([a,b,b]) for a,b in product(range(2),repeat=2)),
                                       key=lambda row: row["utility"])
            arms["content_oracle"] = max((pay(list(reply)) for reply in product(range(2),repeat=3)),
                                         key=lambda row: row["utility"])
            assert max(arm["utility"] for arm in arms.values()) <= arms["content_oracle"]["utility"] + 1e-8
            result.append({"grid": group, "q_first": q0,"q_reply": q1,"price": price,"prior": prior,
                           "policy": arms})
    summary = {}
    for grid in GRIDS:
        rows = [r["policy"] for r in result if r["grid"] == grid]
        summary[grid] = {name: {
            **{metric: round(mean(r[name][metric] for r in rows),8)
               for metric in ("release","cost","utility")},
            "oracle_matches": sum(r[name]["utility"] == r["content_oracle"]["utility"] for r in rows),
            "wins_over_arrival": sum(r[name]["utility"] > r["arrival_only"]["utility"] for r in rows)
        } for name in rows[0]}
    return {"metadata": case, "summary": summary, "rows": result}


def run(spec):
    cases, stress = case_banks()
    trained = {held: train(cases, peers) for held,peers in spec["folds"].items()}
    archived = read(BRIDGE/"results.json")["summary"]
    trials = {key: evaluate(case,trained[key]) for key,case in cases.items()}
    for grid, rows in trials["2739"]["summary"].items():
        assert rows["arrival_only"]["utility"] == archived[grid]["best_arrival_only"]["utility"]
        assert rows["content_oracle"]["utility"] == archived[grid]["content_oracle"]["utility"]
    return {"calibration": trained, "held": trials, "stress": {
        key: evaluate(case,trained["2739"]) for key,case in stress.items()
    }}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    spec = plan()
    if not args.plan:
        assert spec == read(HERE/"plan.json")
    print(json.dumps(spec if args.plan else run(spec), indent=2))
