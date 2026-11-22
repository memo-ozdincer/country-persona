"""Apply the frozen binary authority decoder to an unused negotiation family."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
FACTS=HERE/"facts.json"
LOCK=HERE/"guard-transfer-lock.json"
sys.path.insert(0,str(ROOT/"judge"))
import authority_archive_binary as built

runtime=built.source.prior.runner


def suite():
    data=built.source.prior.load(FACTS)
    for pair in data["guard_pairs"]:
        evidence={k:data["numbered_evidence"][k] for k in pair["evidence"]}
        for expected,field in (("clear","bounded"),("failed","foil")):
            for i,layout in enumerate((tuple(built.CHOICES),tuple(reversed(built.CHOICES)))):
                body={"evidence":evidence,"candidate_clause":pair[field],
                      "choices":dict(zip("AB",(built.CHOICES[k] for k in layout),strict=True))}
                yield {"id":f"{pair['id']}/{expected}/{i}","labels":"AB","profiles":layout,"messages":[
                    {"role":"system","content":built.source.SYSTEM},
                    {"role":"user","content":json.dumps(body,ensure_ascii=False)},
                ]}


def score(rows):
    data=built.source.prior.load(FACTS)
    counts=Counter()
    test={}
    for pair in data["guard_pairs"]:
        for expected in ("clear","failed"):
            key=f"{pair['id']}/{expected}"
            margins=[]
            for i in range(2):
                row=rows[f"{key}/{i}"]
                logits=dict(zip(row["profiles"],row["label_logits"],strict=True))
                margins.append(logits["failed"]-logits["clear"])
            answers=["failed" if v>0 else "clear" if v<0 else None for v in margins]
            stable=answers[0] if answers[0]==answers[1] else None
            average=sum(margins)/2
            pooled="failed" if average>0 else "clear" if average<0 else None
            test[key]={"expected":expected,"orders":answers,"margins":margins,"pooled_margin":average,
                       "stable":stable,"pooled":pooled}
            for decoder,value in (("stable",stable),("pooled",pooled)):
                counts[decoder,"uncertain" if value is None else "correct" if value==expected else "wrong"]+=1
    return {"totals":{"/".join(k):v for k,v in sorted(counts.items())},"cases":test}


def hashes():
    return {**built.hashes(),**{str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest()
                              for p in (Path(__file__).resolve(),FACTS)}}


if __name__=="__main__":
    with patch.multiple(runtime,LOCK=LOCK,LABELS="AB",suite=suite,score=score,hashes=hashes):
        runtime.main()
