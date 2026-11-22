"""Test whether a conservative score cutoff survives a docket change."""
import json
from pathlib import Path
from hashlib import sha256

HERE=Path(__file__).resolve().parent
FILES={
    "2475":HERE.parents[1]/"disability-2475-transfer/bound-comparison/scored.json",
    "2721":HERE/"scores.json",
}


def data():
    d=json.loads(FILES["2475"].read_text())["classification"]["rows"]
    af=json.loads(FILES["2721"].read_text())["observations"]
    return {
        "2475":{key:(value["truth"],sum(x["support_minus_unsupported"] for x in value["orders"].values())/2)
                 for key,value in d.items()},
        "2721":{key:(value["supported"],sum(value["margins"].values())/2) for key,value in af.items()},
    }


def classify(rows,cutoff):
    selected=[key for key,(_,margin) in rows.items() if margin>cutoff]
    return {"supported_admitted":sum(rows[key][0] for key in selected),
            "unsupported_admitted":sum(not rows[key][0] for key in selected),
            "admitted":selected}


def run():
    rows=data()
    results={}
    for train,test in (("2475","2721"),("2721","2475")):
        # This is the lowest cutoff rejecting every unsupported fitting candidate.
        cutoff=max(margin for supported,margin in rows[train].values() if not supported)
        own=classify(rows[train],cutoff)
        assert own["unsupported_admitted"]==0
        held=classify(rows[test],cutoff)
        results[f"{train}_to_{test}"]={
            "cutoff":cutoff,"fitting":own,"held":held,"zero_cutoff_held":classify(rows[test],0.)}
    return {"folds":results,"files_sha256":{name:sha256(path.read_bytes()).hexdigest() for name,path in FILES.items()}}


if __name__=="__main__":
    print(json.dumps(run(),indent=2))
