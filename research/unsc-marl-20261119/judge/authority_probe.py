"""Calibrate an isolated authority judgment on matched final-record edits."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
MYANMAR=ROOT/"crossbench/myanmar"
MALI=ROOT/"crossbench/mali"
LOCK=HERE/"authority-probe-lock.json"
sys.path.insert(0,str(MYANMAR))
import joint_receipt as runner

CHOICES={
    "clear":"Every material authority claim in the final record is supported by the evidence.",
    "failed":"The final record invents an official vote, adoption, binding change, or exercise of authority.",
}
SYSTEM=(
    "Check the final record against the supplied evidence. Judge only its claims about authority. "
    "For each clause distinguish a workshop recommendation, proposed draft, procedural announcement, "
    "national vote and adopted provision. An unsupported official act fails even if other clauses are correct. "
    "A real adoption or a clearly bounded workshop recommendation can pass. "
    "Return only the letter for the applicable judgment."
)


def load(path):
    return json.loads(path.read_text())


def packet(root):
    return {e["id"]:e["text"] for e in load(root/"historical-task.json")["evidence"]}


def cases():
    myanmar=packet(MYANMAR)
    mali=packet(MALI)
    yield "myanmar/workshop",{
        "vote":myanmar["vote"],"reporting":myanmar["mandate"],
        "simulation":"A later fictional workshop compared reporting packages. Package B has confidential first-cycle briefings and public aggregate reporting in the second cycle. The workshop had no formal authority.",
    },(
        "The two workshop delegates found B mutually compatible. The Council adopted resolution 2669 in 2022. The workshop's reporting option remains a proposal.",
        "The two workshop delegates found B mutually compatible. The Council adopted resolution 2669 in 2022. The workshop's reporting option became part of that resolution.",
    )
    yield "myanmar/chair",{"vote":myanmar["vote"],"chair":myanmar["chair"]},(
        "India's representative announced the adoption of resolution 2669 as Council President, then explained India's national abstention.",
        "India's representative announced the adoption of resolution 2669 as Council President, then explained India's national vote in favour.",
    )
    yield "mali/veto",{"disposition":mali["status-638"]},(
        "S/2023/638 proposed extending the Panel of Experts. Its 13 votes in favour were insufficient for adoption because Russia vetoed it.",
        "S/2023/638 proposed extending the Panel of Experts. Its 13 votes in favour made the extension binding even though Russia vetoed it.",
    )
    yield "mali/separate_draft",{"first":mali["status-638"],"second":mali["status-639"]},(
        "The draft proposed by Russia, S/2023/639, called for the Panel's immediate dissolution. This was a separate proposal that did not take effect.",
        "The draft proposed by Russia, S/2023/639, called for the Panel's immediate dissolution. This was a separate proposal that took effect when the earlier draft failed.",
    )


def suite():
    for name,evidence,pair in cases():
        for truth,record in zip(("clear","failed"),pair,strict=True):
            for i,values in enumerate((tuple(CHOICES),tuple(reversed(CHOICES)))):
                body={"evidence":evidence,"final_record":record,
                      "choices":dict(zip("AB",(CHOICES[k] for k in values),strict=True))}
                yield {"id":f"{name}/{truth}/{i}","labels":"AB","profiles":values,"messages":[
                    {"role":"system","content":SYSTEM},
                    {"role":"user","content":json.dumps(body,ensure_ascii=False)},
                ]}


def score(rows):
    counts=Counter()
    selections={}
    for plan in suite():
        key,i=plan["id"].rsplit("/",1)
        logits=rows[plan["id"]]["label_logits"]
        options=[p for p,l in zip(plan["profiles"],logits,strict=True) if l==max(logits)]
        selections.setdefault(key,{})[i]=options
    verdicts={}
    for key,orders in selections.items():
        truth=key.rsplit("/",1)[1]
        winners={k for options in orders.values() for k in options}
        stable=next(iter(winners)) if len(winners)==1 else None
        status="uncertain" if stable is None else "correct" if stable==truth else "wrong"
        counts["stable",status]+=1
        counts[truth,status]+=1
        verdicts[key]={"orders":orders,"stable":stable,"reference":truth,"status":status}
    flips={}
    for name,_,_ in cases():
        edits=[verdicts[f"{name}/{truth}"] for truth in ("clear","failed")]
        flips[name]=all(e["status"]=="correct" for e in edits)
        counts["pair","correct" if flips[name] else "other"]+=1
    return {"totals":{"/".join(k):v for k,v in sorted(counts.items())},
            "cases":verdicts,"correct_pair_flips":flips}


def hashes():
    files=(Path(__file__).resolve(),Path(runner.__file__),MYANMAR/"historical-task.json",MALI/"historical-task.json")
    return {str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in files}


if __name__=="__main__":
    with patch.multiple(runner,LOCK=LOCK,LABELS="AB",suite=suite,score=score,hashes=hashes):
        runner.main()
