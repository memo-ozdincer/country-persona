"""Choose a partner-value model from the evidence in the receipt history."""
from hashlib import sha256
import json
from math import sqrt
from pathlib import Path
from statistics import mean

import numpy as np

import unknown_partner as known

HERE=Path(__file__).resolve().parent
GRID=np.linspace(0,1,21)


def switch(counts, likelihood, utility, pure, excluded, sampled, choose):
    table = GRID[:,None]*likelihood[0] + (1-GRID[:,None])*likelihood[1]
    mix, out_of_support = known.posterior(counts,table)
    alpha = mix @ GRID
    candidates = choose(np.column_stack((alpha,1-alpha)))
    default = choose(np.full((len(counts),2),.5))
    incumbent = choose(pure)
    quantiles = np.cumsum(mix,axis=1)
    lower = GRID[(quantiles>=.10).argmax(-1)]
    upper = GRID[(quantiles>=.90).argmax(-1)]
    states = np.arange(utility.shape[1])
    wins = utility[:,states,candidates]-utility[:,states,default]
    confident = ((lower[:,None]*wins[0]+(1-lower[:,None])*wins[1]) >= -1e-12) & (
                (upper[:,None]*wins[0]+(1-upper[:,None])*wins[1]) >= -1e-12)
    careful = np.where(confident,candidates,default)
    selection = np.where(excluded[:,None],careful,incumbent)
    selection = np.where(out_of_support[:,None],sampled,selection)
    return {"convex-only": candidates, "support-selector":selection}


if __name__=="__main__":
    output=known.run(extension=switch)
    overall = {}
    for horizon in known.HORIZONS:
        rows = [r["horizons"][horizon] for grid in output["conditions"].values()
                for channel in grid.values() for r in channel.values()]
        error = sqrt(sum(row["selector_standard_error"]**2 for row in rows))/len(rows)
        overall[horizon] = dict(conditions=len(rows),
                                net={key:mean(row["net"][key] for row in rows) for key in rows[0]["net"]},
                                paired_history_sampling_se=error)
    output["overall"] = overall
    files=(Path(__file__),HERE/"mixture-partner-protocol.md",HERE/"first-unknown-partner.json")
    output["selector_hashes"]={p.name:sha256(p.read_bytes()).hexdigest() for p in files}
    print(json.dumps(output,indent=2))
