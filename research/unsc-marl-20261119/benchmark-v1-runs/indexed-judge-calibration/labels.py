"""Check model labels before rebinding, including structurally rejected replies."""
from collections import Counter
import json

import indexed


def audit():
    rows=indexed.live.prior.report.load(indexed.OUT/"tokens.jsonl")
    modes=indexed.live.fixtures()
    result={}
    for mode,anchors in modes.items():
        counts=Counter()
        mismatches=[]
        for row in rows:
            if row["mode"]!=mode:
                continue
            expected=anchors[row["id"]][1]
            counts["target_labels"]+=len(expected)
            text=row["reply"]["text"]
            try:
                value=json.loads(indexed.unwrap(text))
                observed=({r["id"]:r["status"] for r in value["units"]} | {"guard":value["guard"]["status"]}
                          if mode=="final" else {r["id"]:r["points"] for r in value["ratings"]})
            except (ValueError,KeyError,TypeError):
                continue
            counts["parseable_packets"]+=1
            for key,answer in expected.items():
                counts["labels_present"]+=int(key in observed)
                counts["correct"]+=int(observed.get(key)==answer)
                if observed.get(key)!=answer:
                    mismatches.append({"packet":row["id"],"label":key,"expected":answer,"observed":observed.get(key)})
        result[mode]={"counts":dict(counts),"mismatches":mismatches}
    return result


if __name__=="__main__":
    print(json.dumps(audit(),indent=2))
