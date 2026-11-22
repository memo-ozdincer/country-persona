"""Report signed label margins before collapsing the two code orders."""
import argparse
import json
from pathlib import Path


def audit(path):
    grouped={}
    for row in map(json.loads,(path/"predictions.jsonl").read_text().splitlines()):
        a,b=row["label_logits"]
        margin=(a-b) if row["support_code"]=="A" else (b-a)
        item=row["id"].rsplit("/",1)[0]
        group=grouped.setdefault(item,{"reference":row["supports"],"margins":[]})
        group["margins"].append(margin)
    for row in grouped.values():
        assert len(row["margins"])==2
        row["mean_margin"]=sum(row["margins"])/2
        row["predicted"]=True if row["mean_margin"]>0 else False if row["mean_margin"]<0 else None
    rank={}
    for key,row in grouped.items():
        if not row["reference"]:
            continue
        family=key.removesuffix("/supported")
        foil=grouped[f"{family}/foil"]["mean_margin"]
        rank[family]={"supported_margin":row["mean_margin"],"foil_margin":foil,
                      "strictly_ranked":row["mean_margin"]>foil}
    return {"cases":grouped,"ranking":rank,
            "accuracy_with_averaged_margins":sum(row["reference"]==row["predicted"] for row in grouped.values()),
            "correct_relative_ranks":sum(r["strictly_ranked"] for r in rank.values())}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("evidence",type=Path)
    print(json.dumps(audit(p.parse_args().evidence),indent=2))
