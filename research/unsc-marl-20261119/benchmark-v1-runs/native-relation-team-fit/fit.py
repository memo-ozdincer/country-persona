"""Jointly update decentralized routing policies from model-derived terminal points."""
from itertools import product
import json

import numpy as np

from collect_transfer import HERE, SOURCE, TEAM, CLAIMS, WEIGHTS, old, plan, read

team = old.typed.prior.load("native_relation_joint_fit", TEAM / "train_team.py")


def approvals(spec, outputs):
    assert set(outputs) == {x["id"] for x in spec["requests"]}
    result = {}
    for key, pair in spec["pairs"].items():
        margins = {}
        for relation in CLAIMS:
            scores = []
            for card in spec["references"][key]:
                ab = outputs[f"{card}/{relation}/ab"]["logits"]
                ba = outputs[f"{card}/{relation}/ba"]["logits"]
                scores.append(((ab["A"]-ab["B"])+(ba["B"]-ba["A"]))/2)
            margins[relation] = scores
        passing = [rel for rel, values in margins.items() if min(values) > 0]
        chosen = passing[0] if len(passing) == 1 else None
        result[key] = {"expected": pair["expected"], "predicted": chosen,
                       "margins_early_reply": margins, "real": pair["real"]}
    return result


def tables(grades):
    exact = team.tables()
    trusted, audited = (list(exact) for _ in range(2))
    trusted[3], audited[3] = (exact[3].copy() for _ in range(2))
    afghan = read(SOURCE / "results.json")["relations"]
    afghan_rows = {"russia-full": 0, "ghana-full": 1}
    variants = []
    for family, (docket, views) in enumerate(team.PRIVATE.items()):
        for i, view in enumerate(views):
            for j, reply in enumerate(team.ACTIONS):
                key = f"{view}/{reply}"
                if docket == "reform":
                    row = grades[key]
                    expected, chosen = row["expected"], row["predicted"]
                    reference, estimated = (WEIGHTS.get(x, 0) for x in (expected, chosen))
                elif view in afghan_rows:
                    row = afghan[f"{afghan_rows[view]}/{1-j}"]
                    expected, chosen = row["expected"], row["choices"]["mean"]
                    reference, estimated = (22 if x != "none" else 0 for x in (expected, chosen))
                    expected, chosen = (None if x == "none" else x for x in (expected, chosen))
                else:
                    expected, chosen, reference, estimated = None, None, 0, 0
                base = int(exact[3][family, i, j]) - reference
                assert base >= 0
                measured = base + estimated
                faithful = measured if not chosen or chosen == expected else 0
                trusted[3][family, i, j] = measured
                audited[3][family, i, j] = faithful
                variants.append({"docket": docket, "key": key, "expected": expected, "predicted": chosen,
                                 "standalone": base, "trusted": measured, "audited": faithful,
                                 "authored": base + reference})
    return {"trusted_native": trusted, "audited_native": audited, "ideal_authored": exact}, variants


def arrival_ceiling(table, data):
    public, first_only, last_only, both, observed = table
    d = list(team.PRIVATE).index(data["family"])
    q0, q1, cost = (data[key] for key in ("q_first", "q_reply", "cost"))
    mass = np.array(data["private_prior"])
    candidates = []
    for b0, b1 in product((0, 1), repeat=2):
        absent = (1-q1)*public[d] + q1*last_only[d, b0]
        present = (1-q1)*first_only[d] + q1*both[d, :, b1]
        gain = (present - absent)*q0 - cost
        candidates.append(float(mass @ (absent + np.maximum(gain, 0))))
    return round(max(candidates), 8)


def compare(table, trained, baseline):
    current = team.evaluate(table, *trained)
    existing = team.evaluate(table, *baseline)
    records = []
    for model, old in zip(current, existing, strict=True):
        anchors = {k: v for k, v in model.items() if k != "policies"}
        assert all(old[k] == v for k, v in anchors.items())
        data = model["policies"]
        records.append(anchors | {
            "native_fit": data["learned"],
            "archival_fit": old["policies"]["learned"],
            "native_fit_fixed_reply": data["learned_sender_fixed_fund"],
            "best_arrival_only": {"utility": arrival_ceiling(table, anchors)},
            "oracle": data["oracle"],
        })
    return {"held": records, "mean_utility": {
        subset: {name: round(float(np.mean([r[name]["utility"] for r in records
                                            if subset == "all" or r["family"] == subset])), 8)
                 for name in ("native_fit", "archival_fit", "native_fit_fixed_reply", "best_arrival_only", "oracle")}
        for subset in ("all", *team.PRIVATE)
    }}


def run():
    spec = plan()
    assert spec == read(HERE / "plan.json")
    grades = approvals(spec, read(HERE / "verified.json")["outputs"])
    banks, rows = tables(grades)
    original = read(TEAM / "results.json")["history"]
    baseline = [np.array(original[-1][key]) for key in ("sender", "receiver")]
    sender, receiver, history = team.train(banks["trusted_native"])
    return {"grades": grades, "terminal_rows": rows, "optimizer_updates": team.UPDATES,
            "history": history, "archival_history": original,
            "evaluation": {k: compare(v, (sender, receiver), baseline) for k, v in banks.items()}}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
