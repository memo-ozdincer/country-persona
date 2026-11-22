"""Replay two existing controllers without fitting to the Afghanistan packet."""
from itertools import product
import json
from pathlib import Path

import numpy as np

import replay as new

RUNS = new.HERE.parent
ORIGINAL = RUNS / (
    "cooperative-rollout-fit/evidence-choice/receipt-conditioned/sampled-return/"
    "listener-residual/private-opener"
)


def run():
    # The old numeric action features are local credit, uniform joint credit,
    # and priority-weighted joint credit. Both early candidates have equal
    # standalone credit here, so the two joint forecasts coincide.
    original = ORIGINAL/"results.json"
    split = ORIGINAL/"split-results.json"
    weights = {
        "fixed": [1.,0.,1.],
        "varied_prior_fit": json.loads(original.read_text())["training"]["varied"]["checkpoints"]["150"]["weights"],
        "separate_links_fit": json.loads(split.read_text())["trace"]["checkpoints"]["150"]["weights"],
    }
    records,_ = new.cases()
    rows = []
    for q,prior in product(new.RATES,new.PRIORS):
        results = {}
        for name,w in weights.items():
            features = {view: np.asarray([[6,22*int(view==action),22*int(view==action)]
                                         for action in (0,1)])/7
                        for view in (None,0,1)}
            policy = {key:int(np.argmax(x@w)) for key,x in features.items()}
            score = float(new.receipt_value(records,q,prior,policy))
            results[name] = {"actions":{"lost":policy[None],"first":policy[0],"second":policy[1]},
                             "released":score}
        ceiling = new.evaluate(records,q,prior)["content_ceiling"]
        assert all(row["released"] == ceiling for row in results.values())
        rows.append({"delivery":float(q),"prior":float(prior),"ceiling":ceiling,"policies":results})
    return {"conditions":rows,"source_sha256": {str(path.relative_to(RUNS)):new.pin(path)
                                                 for path in (original,split,Path(__file__),new.HERE/"results.json")}}


if __name__ == "__main__":
    print(json.dumps(run(),indent=2))
