"""Score four transparent baselines on fields and on the complete handover."""
from collections import Counter, defaultdict
import json

from handover import packets


def controls():
    counts=defaultdict(Counter)
    examples=[]
    for task,key in packets():
        source_text=" ".join(value for value in task["holdings"].values() if value)
        for method in ("preserve draft","verify all","date anywhere","field and evidence"):
            complete=True
            for i,(field,proposed) in enumerate(task["draft"].items()):
                card=list(task["holdings"].values())[i]
                if method=="preserve draft":
                    action,date="confirm",proposed
                elif method=="verify all":
                    action,date="verify",None
                elif method=="date anywhere":
                    action,date=("confirm",proposed) if proposed in source_text else ("verify",None)
                else:
                    # Use semantic text anchors only on supported source card templates.
                    import re
                    pattern={
                        "end of existing UNAMI mandate":r"mandate until ([^.]+)",
                        "deadline to deliver the independent strategic review":r"no later than ([^.]+)",
                        "expiry of the renewed sanctions measures":r"2293 \(2016\) until ([^.]+)",
                        "expiry of the Group of Experts mandate":r"Experts mandate to (.+?) and intended"
                    }[field]
                    match=re.search(pattern,card) if card else None
                    date=match[1] if match else None
                    action=("confirm" if proposed==date else "correct") if date else "verify"
                good=(action,date)==(key["actions"][field],key["deliverable"][field])
                counts[method]["correct_fields"]+=good
                counts[method]["unsupported_confirmations"]+=action=="confirm" and key["actions"][field]=="verify"
                if not good and method=="date anywhere" and len(examples)<3:
                    examples.append({"draft":task["draft"],"available":[k for k,v in task["holdings"].items() if v],
                                     "field":field,"prediction":action,"expected":key["actions"][field]})
                complete &= good
            counts[method]["complete_handovers"]+=complete
    return {"baseline_scores":counts,"date_anywhere_failures":examples}


if __name__=="__main__":
    print(json.dumps(controls(),indent=2))
