"""Audit information boundaries and re-optimize arrival-only from fresh branch scores."""
from itertools import product
import json
from statistics import mean

import live


def run():
    case = live.read(live.BASE/"case.json")
    old = live.read(live.WITNESS/"plan.json")["requests"]
    episodes = live.read(live.HERE/"evidence/episodes.json")
    scores = {}
    reply_action = {}
    for row in episodes["branches"]:
        view = row["view"]
        document = row["reply"]
        key = row["setting"], row["arm"], view, row["channel"][0]
        assert reply_action.setdefault(key, document) == document
        assert len(row["record"].split()) <= case["word_cap"]
        if row["arm"] == "arrival":
            assert row["reply_margin"] is None
        sources = json.loads(old[f"{view}/{document}"]["messages"][1]["content"])
        for available, field in ((row["arrived"], "delegate_statement"),
                                 (row["reply_delivered"], "adopted_document")):
            assert (sources[field] in row["record"]) == available
        if not row["arrived"]:
            assert row["reply_observation"] == 0 and row["reply_margin"] is None
        if row["arrived"] and row["reply_delivered"]:
            assert scores.setdefault((view, document), row["released"]) == row["released"]

    assert len(scores) == 6
    public = sum(item["weight"] for item in case["public"])
    optimized = []
    for mass, summary in zip(live.PRIORS, episodes["summaries"], strict=True):
        best = -float("inf")
        for absent, present in product(case["late"], repeat=2):
            default = public + live.Q * case["late"][absent]["weight"]
            values = []
            for view in case["early"]:
                marginal = (1-live.Q)*(public+case["early"][view]["weight"])+live.Q*scores[view, present]
                values.append(default + max(0, live.Q*(marginal-default)-live.PRICE))
            best = max(best, sum(p*v for p,v in zip(mass, values, strict=True)))
        optimized.append({"prior": mass, "arrival_reoptimized": round(best, 8),
                          "gain_over_reoptimized": round(summary["arms"]["learned"]["utility"]-best, 8)})
    return {"branch_records": len(episodes["branches"]),
            "fresh_pair_scores": {f"{key[0]}/{key[1]}": value for key,value in scores.items()},
            "both_arms_always_attempt_first_send": all(row["sent"] for row in episodes["branches"]),
            "optimized": optimized, "mean_gain": mean(row["gain_over_reoptimized"] for row in optimized)}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
