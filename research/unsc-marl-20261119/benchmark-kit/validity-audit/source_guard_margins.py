"""Test fixed pooling of reversed judge scores on the authored claim pairs."""
from hashlib import sha256
import json
from math import exp
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ANNOTATIONS = HERE / "guard-contrast.json"
SETS = ((True, False), (False, True), (True, True), (False, False))


def probabilities(row):
    scores = row["scores"]
    anchor = max(scores)
    weights = [exp(s - anchor) for s in scores]
    total = sum(weights)
    return [w / total for w in weights]


def report(raw):
    rows = {tuple(r["observation"]):r for r in map(json.loads, raw.read_text().splitlines())}
    output = []
    for spec in json.loads(ANNOTATIONS.read_text())["pairs"]:
        name = spec["id"]
        gold = tuple(spec["support"])
        pair = []
        separate = []
        for order in (0, 1):
            joint = probabilities(rows[name,"pair",0,order,False])
            pair.append(dict(zip(SETS if order == 0 else [x[::-1] for x in SETS], joint, strict=True)))
            separate.append(tuple(probabilities(rows[name,"single",i,order,False])[order] for i in (0, 1)))
        merged = {key: sum(p[key] for p in pair)/2 for key in SETS}
        choice = max(merged,key=merged.__getitem__)
        pooled = tuple((a+b)/2 for a,b in zip(*separate,strict=True))
        individual = tuple(p > .5 for p in pooled)
        output.append({"id":name,"reference":gold, "pair_pooled":choice,"single_pooled":individual,
                       "pair_scores":[{"allowed_set":k,"probability":v} for k,v in merged.items()],
                       "single_support_scores":pooled})
    return {"raw_sha256":sha256(raw.read_bytes()).hexdigest(),
            "pair_exact":sum(x["pair_pooled"]==x["reference"] for x in output),
            "single_exact":sum(x["single_pooled"]==x["reference"] for x in output),
            "pairs":output}

if __name__=="__main__":
    print(json.dumps(report(Path(sys.argv[1])),indent=2))
