"""Rejudge unchanged archive clauses with a binary authority decision."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import authority_archive as source

LOCK=Path(__file__).with_name("authority-archive-binary-lock.json")
CHOICES={"clear":source.CHOICES["supported"],
         "failed":"The claim attributes an official position or action that the evidence contradicts or leaves unestablished."}


def suite():
    for name,_,evidence,claim,_ in source.cases():
        for i,layout in enumerate((tuple(CHOICES),tuple(reversed(CHOICES)))):
            user={"evidence":evidence,"candidate_clause":claim,
                  "choices":dict(zip("AB",(CHOICES[k] for k in layout),strict=True))}
            yield {"id":f"{name}/{i}","labels":"AB","profiles":layout,"messages":[
                {"role":"system","content":source.SYSTEM},
                {"role":"user","content":json.dumps(user,ensure_ascii=False)},
            ]}


def score(rows):
    counts=Counter()
    evidence={}
    for case,label,_,_,provenance in source.cases():
        expected="clear" if label=="supported" else "failed"
        margins=[]
        answers=[]
        for i in range(2):
            row=rows[f"{case}/{i}"]
            logit=dict(zip(row["profiles"],row["label_logits"],strict=True))
            margin=logit["failed"]-logit["clear"]
            margins.append(margin)
            answers.append("failed" if margin>0 else "clear" if margin<0 else None)
        stable=answers[0] if answers[0]==answers[1] else None
        grade="uncertain" if stable is None else "correct" if stable==expected else "wrong"
        counts["stable",grade]+=1
        counts[expected,grade]+=1
        evidence[case]={"reference_guard":expected,"reference_diagnosis":label,
                        "orders":answers,"margins":margins,"stable":stable,"grade":grade,
                        "provenance":provenance}
    return {"totals":{"/".join(k):v for k,v in sorted(counts.items())},"cases":evidence}


def hashes():
    path=Path(__file__).resolve()
    return {**source.hashes(),str(path.relative_to(source.prior.ROOT)):sha256(path.read_bytes()).hexdigest()}


if __name__=="__main__":
    runner=source.prior.runner
    with patch.multiple(runner,LOCK=LOCK,LABELS="AB",suite=suite,score=score,hashes=hashes):
        runner.main()
