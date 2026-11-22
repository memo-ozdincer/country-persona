"""Fit transferable reply calibration from observed terminal records."""
import argparse
from itertools import product
import json
from pathlib import Path

import numpy as np

from collect_logits import BRIDGE, DONORS, HERE, OPTIONS, RUNS, guard, previous, requests
import fit_transfer as prior

BRIDGE_OUT = BRIDGE.with_name("results.json")
EARLIER = RUNS/"text-only-routing-transfer/results.json"


def plan():
    paths = (Path(__file__), HERE/"plan.json", BRIDGE, BRIDGE_OUT, prior.NATIVE,
             Path(prior.__file__), EARLIER)
    return {"pins": {str(path.relative_to(RUNS.parent)): guard.suite.pin(path) for path in paths},
            "families": list(DONORS), "seed": 24172721, "episodes": 256,
            "send_probability": 0.65, "delivery_probability": 0.65,
            "temperatures": [0.25, 0.5, 1., 2., 4., 8.],
            "neither_offsets": [-4., -2., -1., 0., 1., 2., 4.],
            "penalties": [0., 0.03, 0.1, 0.3],
            "held": prior.prior.plan()["held"]}


def read(path):
    return previous.read(path)


def logits():
    out = guard.historical.report.load(HERE/"evidence/labels.jsonl")
    grouped = {}
    for row, expected in zip(out, requests(), strict=True):
        assert all(row[field] == v for field, v in expected.items())
        values = {label: row["logits"][letter] for letter, label in row["labels"].items()}
        grouped.setdefault(row["id"], []).append(values)
    return {
        ident: {"mean": [sum(row[option] for row in items)/3 for option in OPTIONS], "orders": items}
        for ident, items in grouped.items()
    }


def donor_data():
    banks = {d: prior.donor_payoff(d) for d in prior.DONORS}
    verified = read(BRIDGE_OUT)["records"]
    for docket, case in read(BRIDGE)["cases"].items():
        weights = {row["id"]: row["weight"] for row in case["rubric"]}
        public = sum(weights[key] for key in case["public"])
        first, last = ([
            public+sum(weights.get(key, 0) for key in row["record"]) for row in case[side].values()
        ] for side in ("early","late"))
        released = [verified[f"{docket}/{a}/{b}"]["audited_score"]
                    for a, b in product(case["early"], case["late"])]
        banks[docket] = public, first, last, released
    return banks


def donor_episodes(spec, banks):
    data = {}
    for name, (public, first, last, released) in banks.items():
        rng = np.random.default_rng(spec["seed"]+int(name))
        pairs = {}
        trace = []
        for i in range(spec["episodes"]):
            view, reply = int(rng.integers(len(first))), int(rng.integers(len(last)))
            attempt, outward, inward = rng.random(3)
            front = attempt < spec["send_probability"] and outward < spec["delivery_probability"]
            back = inward < spec["delivery_probability"]
            if front and back:
                score = released[2*view+reply]
                pairs[view, reply] = score-(first[view]+last[reply]-public)
            else:
                score = first[view] if front else last[reply] if back else public
            trace.append({"view": view, "reply": reply, "first_arrived": bool(front),
                          "reply_arrived": bool(back), "score": score})
        marks = {}
        for i in range(len(first)):
            if (i,0) in pairs and (i,1) in pairs:
                residuals = [pairs[i,0], pairs[i,1]]
                assert all(x >= 0 for x in residuals) and sum(x > 0 for x in residuals) <= 1
                marks[f"{name}/{i}"] = {"residuals": residuals,
                                      "answer": int(np.argmax(residuals)) if max(residuals) else 2}
        data[name] = {"marks": marks, "trace": trace}
    return data


def probabilities(values, temperature, neither_offset):
    scaled = np.asarray(values) / temperature + np.array([0.,0.,neither_offset])
    z = np.exp(scaled-scaled.max())
    return z/z.sum()


def loss(rows, mapping, temp, offset):
    return float(np.mean([-np.log(probabilities(mapping[key]["mean"], temp, offset)[label])
                          for key, label in rows.items()]))


def learn(spec, data, mapping):
    panels = {d: {key: row["answer"] for key, row in data[d]["marks"].items()} for d in spec["families"]}
    configs = list(product(spec["temperatures"], spec["neither_offsets"]))

    def train(panel, strength):
        return min(configs, key=lambda c: loss(panel, mapping, *c) +
                   strength*(np.log(c[0])**2 + c[1]**2))

    comparison = {}
    for strength in spec["penalties"]:
        folds = {}
        for held in spec["families"]:
            training = {key: answer for donor, rows in panels.items() if donor != held
                        for key, answer in rows.items()}
            config = train(training, strength)
            folds[held] = {"temperature": config[0], "offset": config[1],
                           "loss": loss(panels[held], mapping, *config)}
        comparison[strength] = {"folds": folds, "mean_loss": float(np.mean([row["loss"] for row in folds.values()]))}
    best = min(comparison, key=lambda strength: comparison[strength]["mean_loss"])
    params = train({k: v for p in panels.values() for k, v in p.items()}, best)
    all_bonuses = [v for donor in data.values() for mark in donor["marks"].values()
                   for v in mark["residuals"] if v > 0]
    assert all_bonuses
    return {"regularization": best, "temperature": params[0], "offset": params[1],
            "comparison_value": float(np.mean(all_bonuses)), "donor_cv": comparison}


def offers(mapping, calibration):
    scale = calibration["comparison_value"]
    groups = {"2417": "2417", "held_wording": "paraphrased"}
    results = {}
    for target, panel in (*groups.items(), ("fiction","fiction")):
        rows = [(ident, row) for ident,row in mapping.items() if ident.startswith(panel+"/")]
        values = {}
        for ident, row in rows:
            mean = row["mean"]
            base = probabilities(mean, 1., 0.)
            learned = probabilities(mean, calibration["temperature"], calibration["offset"])
            winner = np.eye(3)[int(np.argmax(mean))]
            values[ident] = {"fixed_hard": winner.tolist(), "fixed_probabilities": base.tolist(),
                             "calibrated": learned.tolist()}
        by_method = {method: [scale*value for row in values.values() for value in row[method][:2]]
                     for method in next(iter(values.values()))}
        results[target] = {"class_scores": values, "predictions": by_method}
    return results


def fitted(spec):
    mapping = logits()
    data = donor_episodes(spec, donor_data())
    calibration = learn(spec, data, mapping)
    credits = offers(mapping, calibration)
    return {"logits": mapping, "trajectory_log": data, "calibration": calibration,
            "offers": credits, "routes": prior.make_routes(spec, credits, prior.core_2417())}


def checked_scores(spec):
    started = read(HERE/"fit.json")
    archive = read(EARLIER)
    scored = prior.score(spec, started["routes"], np.array(archive["reference"]))
    comparisons = ("donor_fit_256/peer", "both_features/peer", "lexical/peer", "oracle/arrival_only", "oracle/peer")
    return {"reference": archive["reference"], "evaluations": scored,
            "prior_comparisons": {panel: {name: row["summary"][name] for name in comparisons}
                                  for panel,row in archive["evaluation"].items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan","fit","score"))
    args = parser.parse_args()
    spec = plan()
    if args.mode != "plan":
        assert spec == read(HERE/"fit-plan.json")
    value = {"plan": lambda: spec, "fit": lambda: fitted(spec), "score": lambda: checked_scores(spec)}[args.mode]()
    print(json.dumps(value, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
