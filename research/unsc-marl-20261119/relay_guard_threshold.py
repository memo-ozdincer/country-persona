"""Compare frozen and family-fitted whole-memo decision thresholds."""
from collections import Counter
import json
from pathlib import Path
import sys


def analyze(metrics):
    cases=metrics["cases"]
    margins={k:sum(v["margins"])/len(v["margins"]) for k,v in cases.items()}
    families=sorted({v["family"] for v in cases.values()})

    def extremes(used):
        good=max(margins[k] for k in used if cases[k]["expected"]=="clear")
        bad=min(margins[k] for k in used if cases[k]["expected"]=="failed")
        return {"largest_sound_margin":good,"smallest_flawed_margin":bad,"separable":good<bad}

    def classify(used,threshold):
        totals,traces=Counter(),{}
        for k in used:
            observed="failed" if margins[k]>threshold else "uncertain" if margins[k]==threshold else "clear"
            expected=cases[k]["expected"]
            totals[expected,observed]+=1
            traces[k]={"expected":expected,"observed":observed,"margin":margins[k]}
        return {"counts":{"/".join(k):v for k,v in sorted(totals.items())},"cases":traces}

    transfers={}
    for train in families:
        fit=[k for k in cases if cases[k]["family"]==train]
        held=[k for k in cases if cases[k]["family"]!=train]
        bounds=extremes(fit)
        cut=(bounds["largest_sound_margin"]+bounds["smallest_flawed_margin"])/2
        transfers[train]={"bounds":bounds,"midpoint":cut,
                          "train":classify(fit,cut),"other_family":classify(held,cut)}
    refs={
        key:{"pooled": value["pooled"],"stable":value["stable"],"margin":margins[key]}
        for key,value in cases.items() if key.startswith("reference/")
    }
    return {"scope":"Retrospective threshold sensitivity on the same scores. Half-sample threshold transfer is a diagnostic. The original threshold remains zero.",
            "entire_panel":extremes(cases),"zero_threshold":classify(cases,0),
            "midpoint_transfers":transfers,"reference_controls":refs}


if __name__=="__main__":
    print(json.dumps(analyze(json.loads(Path(sys.argv[1]).read_text())),indent=2))
