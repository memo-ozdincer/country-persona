"""Measure frozen policy transfer with explicit mappings of document actions."""
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
TARGET = RUNS / "value-routing-docket-transfer"
DONOR = RUNS / "delisting-2744"
sys.path.insert(0, str(TARGET))
fit = SimpleNamespace(**runpy.run_path(str(TARGET / "fit.py")))

team = fit.team


def digest(path):
    from hashlib import sha256
    return sha256(path.read_bytes()).hexdigest()


def plan():
    target = fit.read(TARGET/"plan.json")
    donor = fit.read(DONOR/"case.json")
    case = target["cases"]["2739"]
    source = fit.read(DONOR/"results.json")["history"][-1]
    weights = {row["id"]: row["weight"] for row in case["rubric"]}
    value = {name: sum(weights.get(key, 0) for key in row["record"])
             for name, row in case["late"].items()}
    paths = (Path(__file__), HERE/"protocol.md", DONOR/"case.json", DONOR/"results.json",
             TARGET/"plan.json", TARGET/"verified.json", TARGET/"results.json",
             TARGET/"lower-price-results.json", TARGET/"fit.py", Path(team.__file__))
    return {
        "target": "2739", "donor": "2744",
        "source_views": list(donor["early"]), "source_documents": list(donor["late"]),
        "target_views": list(case["early"]), "target_documents": list(case["late"]),
        "sender_binding": {"full": "a3plus", "objection": "malta", "voted-only": "switzerland"},
        "document_binding": {"review": "relational", "authority": "standalone"},
        "silent_reply": max(value, key=value.get), "local_reply_weights": value,
        "send_eligible": [bool(set(row["record"]) & (set(weights) - set(case["public"])))
                          for row in case["early"].values()],
        "sender_weights": source["sender"][1], "receiver_weights": source["receiver"][1],
        "grid": {"original": list(team.TEST_PRICES), "lower": [1, 3, 5]},
        "pins": {str(path.relative_to(RUNS)): digest(path) for path in paths},
    }


def run(spec):
    target = fit.read(TARGET/"plan.json")["cases"]
    outputs = fit.read(TARGET/"verified.json")["outputs"]
    _, bank, _, records = fit.bank(target, outputs)
    base, first, last, both, observed = (array[1] for array in bank)
    assert list(target)[1] == spec["target"]
    assert list(observed) == [2, 1, 1]
    doc_names = spec["target_documents"]
    source_actions = np.greater(spec["receiver_weights"], 0).astype(int)
    translated = [
        doc_names.index(spec["document_binding"][spec["source_documents"][a]]) for a in source_actions
    ]
    fallback = [doc_names.index(spec["silent_reply"]), *translated[1:]]
    aligned = np.array([spec["sender_weights"][spec["source_views"].index(spec["sender_binding"][view])]
                        for view in spec["target_views"]])
    raw = np.array(spec["sender_weights"])
    local_mask = np.array(spec["send_eligible"])
    frozen_receivers = {"positional": source_actions.tolist(), "semantic": translated, "semantic_default": fallback}
    settings = []
    for group, prices in spec["grid"].items():
        for q0, q1, cost, prior in product(team.TEST_DELIVERY, team.TEST_DELIVERY, prices, team.TEST_PRIORS):
            mass = np.array(prior)
            features = team.features(q0, q1, cost)

            def pay(send, reply):
                absent = (1-q1)*base + q1*last[reply[0]]
                present = (1-q1)*first + q1*both[np.arange(len(observed)), np.asarray(reply)[observed]]
                gain = q0*(present-absent)-cost
                if send is None:
                    send = gain > 0
                release = mass @ (absent+send*q0*(present-absent))
                spending = cost*(mass @ send)
                return {"utility": round(float(release-spending), 8), "release": round(float(release), 8),
                        "cost": round(float(spending), 8), "send": [int(x) for x in send],
                        "reply": [int(x) for x in reply]}

            transferred = {key: pay((raw if key == "positional" else aligned) @ features > 0, reply)
                           for key, reply in frozen_receivers.items()}
            transferred["semantic_default_novelty"] = pay((aligned @ features > 0) & local_mask, fallback)
            transferred["target_best_sender_fixed_receiver"] = pay(None, fallback)
            transferred["best_arrival_only"] = max(
                (pay(None, [a0,a1,a1]) for a0,a1 in product(range(2), repeat=2)), key=lambda x: x["utility"]
            )
            transferred["content_oracle"] = max(
                (pay(None, reply) for reply in product(range(2), repeat=3)), key=lambda x: x["utility"]
            )
            assert all(value["utility"] <= transferred["content_oracle"]["utility"] + 1e-7
                       for value in transferred.values())
            settings.append({"group": group, "q_first": q0, "q_reply": q1, "price": cost,
                             "prior": prior, "policies": transferred})

    summary = {}
    for group in spec["grid"]:
        rows = [row["policies"] for row in settings if row["group"] == group]
        assert len(rows) == 96
        summary[group] = {
            name: {**{metric: round(mean(row[name][metric] for row in rows), 8)
                      for metric in ("utility", "release", "cost")},
                   "wins_over_arrival": sum(row[name]["utility"] > row["best_arrival_only"]["utility"]
                                            for row in rows),
                   "short_of_oracle": sum(row[name]["utility"] < row["content_oracle"]["utility"] for row in rows)}
            for name in rows[0]
        }
    archive = fit.read(TARGET/"results.json")["comparison"]["mean_utility"]["2739"]
    lower = fit.read(TARGET/"lower-price-results.json")["results"]["mean_utility"]["2739"]
    for group, archived in (("original", archive), ("lower", lower)):
        assert summary[group]["content_oracle"]["utility"] == archived["oracle"]
        assert summary[group]["best_arrival_only"]["utility"] == archived["best_arrival_only"]
    return {"receiver_actions": frozen_receivers,
            "observations": dict(zip(spec["target_views"], observed.tolist(), strict=True)),
            "pair_scores": {key: row["audited_score"] for key, row in records.items() if key.startswith("2739/")},
            "summary": summary, "settings": settings}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    spec = plan()
    if not args.plan:
        assert spec == fit.read(HERE/"plan.json")
    print(json.dumps(spec if args.plan else run(spec), indent=2))
