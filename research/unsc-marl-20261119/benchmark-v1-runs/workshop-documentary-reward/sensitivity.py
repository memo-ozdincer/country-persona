"""Repeat the finite policy fit with conservative partial-record credit."""
from itertools import product
import json
from statistics import mean

import numpy as np

import fit


def run():
    data=fit.build.e.read(fit.HERE/"bank.json")
    scenarios=[]
    for family,order,rate,price in product(data,(0,1),fit.RATES,fit.PRICES):
        table=fit.prepare(data[family]["cases"],order,rate,price)
        indices,mass,points,certified,cost=table
        points=np.where(points==56,42,points)
        conservative=(indices,mass,points,certified,cost)
        arms={kind:fit.fit(conservative,kind) for kind in ("decision","documentary")}
        scenarios.append({"family":family,"order":order,"rate":rate,"cost":price,"fit":arms})
    fields=("released","certified","attempts","documentary","decision")
    return {"partial_score":42,"means":{mode:{field:mean(row["fit"][mode]["score"][field] for row in scenarios)
            for field in fields} for mode in ("documentary","decision")},"rows":scenarios}


if __name__=="__main__":
    print(json.dumps(run(),indent=2))
