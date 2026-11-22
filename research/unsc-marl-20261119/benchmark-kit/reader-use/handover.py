"""Build dated handover tasks by corrupting a working memo and withholding evidence."""
import argparse
from collections import Counter
from itertools import product
import json
from pathlib import Path

CROSS=Path(__file__).resolve().parents[2]/"crossbench"
CASES={
    "unami2023": [
        ("end of existing UNAMI mandate","31 May 2024","TERM"),
        ("deadline to deliver the independent strategic review","31 March 2024","REVIEW")],
    "drc2023": [
        ("expiry of the renewed sanctions measures","1 July 2024","SANCTIONS"),
        ("expiry of the Group of Experts mandate","1 August 2024","EXPERTS")]
}


def packets():
    for family, fields in CASES.items():
        case=json.loads((CROSS/family/"case.json").read_text())
        if family=="unami2023":
            cards={k:v for desk in case["roles"].values() for k,v in desk.items()}
        else:
            cards={k:v["source"]+". "+v["card"] for k,v in case["sources"].items()}
        for _,date,key in fields:
            assert date in cards[key]
        for flips in product(range(2),repeat=2):
            for mask in product(range(2),repeat=2):
                draft={}; holdings={}; actions={}; final={}
                for j,(field,date,key) in enumerate(fields):
                    draft[field]=fields[j^flips[j]][1]
                    holdings[key]=cards[key] if mask[j] else None
                    # The DRC Experts card also gives 1 July as a review/action date.
                    # That alone establishes no sanctions-expiry date.
                    actions[field]=("correct" if flips[j] else "confirm") if mask[j] else "verify"
                    final[field]=date if mask[j] else None
                yield {"family":family,"draft":draft,"holdings":holdings},{"actions":actions,"deliverable":final}


def render():
    inputs=[]; keys=[]
    totals=Counter()
    for i,(packet,key) in enumerate(packets()):
        task=("Prepare a handover for a colleague scheduling the next Council action. For each "
              "draft field confirm it, correct it and supply the date, or flag it for verification "
              "if the supplied record does not establish that specific date. The working memo "
              "may contain errors. Treat a missing packet as unavailable evidence.")
        inputs.append({"id":i,"instruction":task,**packet})
        keys.append({"id":i,**key})
        for v in key["actions"].values(): totals[v]+=1
    return {"inputs":inputs,"keys":keys,"checks":{"cases":len(CASES),"presentations":len(keys),
            "field_decisions":dict(totals)}}


if __name__=="__main__":
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("output",choices=("inputs","keys","checks"))
    print(json.dumps(render()[cli.parse_args().output],indent=2))
