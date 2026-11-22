"""Grade each unedited record against the sources received in that exact view."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import source_record_review as review
from source_route_fit import CASE


def bundle(directory):
    case=json.loads(CASE.read_text())
    units={review.PREFIX[group]+str(i):text for group,pair in case["criterion_pairs"].items()
           for i,text in enumerate(pair,1)}
    raw={r["id"]:r for r in map(json.loads,(directory/"transcript.jsonl").read_text().splitlines())}
    finals=json.loads((directory/"final-records.json").read_text())[case["family"]]
    assert finals=={k:v["output"] for k,v in raw.items()}
    deck,join={},{}
    for ident, row in raw.items():
        key=sha256(("source-route-memo/"+ident).encode()).hexdigest()[:10]
        packet=json.loads(row["messages"][-1]["content"])["evidence"]
        assert list(packet)==row["evidence_ids"]
        deck[key]={"family":case["family"],"criteria":units,"evidence":packet,"candidate":row["output"]}
        join[key]=ident
    return dict(sorted(deck.items())),join


def assess(directory,annotations):
    deck,join=bundle(directory)
    with patch.object(review,"bundle",new=bundle):
        final=review.score(directory,annotations)
    result={}
    for key,ident in join.items():
        item=deck[key]
        labels=annotations["reviews"][key]["units"]
        source_witnessed=all(k in item["evidence"] for k in ("RU-B","CN-B"))
        common_ground_met=labels["C1"][0]=="met"
        assert not common_ground_met or source_witnessed
        proof_points=7*sum(labels[unit][0]=="met" for unit in ("P1","P2","C1"))
        result[ident]={**final[ident],"common_ground_warrant":source_witnessed,
                       "common_ground_realized":common_ground_met,
                       "realized_routing_units_out_of_21":proof_points}
    return {"scope":annotations["scope"],"records":result,
            "transcript_sha256":sha256((directory/"transcript.jsonl").read_bytes()).hexdigest()}


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory",type=Path)
    cli.add_argument("--annotations",type=Path)
    args=cli.parse_args()
    value=(assess(args.directory,json.loads(args.annotations.read_text())) if args.annotations
           else bundle(args.directory)[0])
    print(json.dumps(value,indent=2,ensure_ascii=False))
