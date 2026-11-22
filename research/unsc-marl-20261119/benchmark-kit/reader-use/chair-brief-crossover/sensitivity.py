"""Identify comparisons that depend on weights or speaker order."""
from itertools import product
import json
from audit import data, masked, HERE
from run import trace


def summarize():
    rows=data()
    marks=json.loads((HERE/"marks.json").read_text())
    def bits(key):
        return [s is not None for s in marks[masked(key)]["spans"]]
    comparisons=[]
    for family in ("guinea","libya"):
        for j in (0,1):
            peer=bits(trace(family,"peer",j)[2])
            independent=bits(trace(family,"independent",j)[2])
            contrasts=[int(p)-int(i) for p,i in zip(peer,independent,strict=True)]
            # Weight each criterion 1 or 2 before normalization to 70.
            # A ratio of affine functions has extrema at box vertices.
            gains=[70*sum(d*w for d,w in zip(contrasts,weights,strict=True))/sum(weights)
                   for weights in product((1,2),repeat=len(peer))]
            comparisons.append({"docket":family,"opening":j,"peer_only":[i+1 for i,x in enumerate(contrasts) if x==1],
                                "independent_only":[i+1 for i,x in enumerate(contrasts) if x==-1],
                                "equal_weight_delta":10*sum(contrasts),
                                "relative_weight_1_to_2_range":[round(min(gains),2),round(max(gains),2)]})
    return comparisons


if __name__=="__main__":
    print(json.dumps(summarize(),indent=2))
