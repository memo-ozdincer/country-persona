"""Compare binary and direct-contrast judgments on the frozen reserve panel."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import run as base

HERE=Path(__file__).resolve().parent
RESERVE=HERE/"reserve.json"
CONTRAST=("Read the evidence and highlighted quote. Choose the claim supported by that quote. "
          "A supported claim preserves actor, modality, condition, quantifier and authority. "
          "Judge the claims on evidence, not fluency or which is longer. Respond with a single letter A or B.")


def serialize(x):
    return json.dumps(x,ensure_ascii=False,separators=(",",":"))


def suite():
    for item in json.loads(RESERVE.read_text())["pairs"]:
        common={"source":item["source"],"highlighted_quote":item["quote"]}
        assert item["quote"] in item["source"]
        for category in ("supported","foil"):
            for invert in (False,True):
                texts=("The quote establishes the entire claim.","The quote does not establish the claim.")
                codes=dict(zip(("A","B"),texts[::-1] if invert else texts,strict=True))
                payload={**common,"candidate_claim":item[category],"decision_codes":codes}
                yield {"id":f"binary/{item['id']}/{category}/{int(invert)}",
                       "support_code":"B" if invert else "A","supports":category=="supported",
                       "messages":[{"role":"system","content":base.SYSTEM},
                                   {"role":"user","content":serialize(payload)}]}
        for invert in (False,True):
            order=("foil","supported") if invert else ("supported","foil")
            claims=dict(zip(("A","B"),[item[k] for k in order],strict=True))
            yield {"id":f"contrast/{item['id']}/{int(invert)}",
                   "support_code":"B" if invert else "A","supports":True,
                   "messages":[{"role":"system","content":CONTRAST},
                               {"role":"user","content":serialize({**common,"candidate_claims":claims})}]}


def score(rows):
    binary,paired={},{}
    for item in suite():
        id_=item["id"]
        a,b=rows[id_]["label_logits"]
        signed=(a-b) if item["support_code"]=="A" else b-a
        dest=binary if id_.startswith("binary/") else paired
        dest.setdefault(id_.rsplit("/",1)[0],[]).append(signed)
    binary_report={}
    for id_,margins in binary.items():
        gold=id_.endswith("/supported")
        average=sum(margins)/2
        votes=[m>0 if m!=0 else None for m in margins]
        stable=votes[0] if votes[0]==votes[1] else None
        binary_report[id_]={"gold":gold,"margins":margins,"average":average,"stable":stable}
    panel=json.loads(RESERVE.read_text())
    details={}
    for item in panel["pairs"]:
        id_=item["id"]
        positive=binary_report[f"binary/{id_}/supported"]
        foil=binary_report[f"binary/{id_}/foil"]
        pair=paired[f"contrast/{id_}"]
        details[id_]={"separately_judged_rank_correct":positive["average"]>foil["average"],
                      "contrast_margins":pair,"contrast_stably_correct":all(m>0 for m in pair),
                      "contrast_order_disagrees":(pair[0]>0)!=(pair[1]>0)}
    invalid={r["id"]:r["quote"] in r["source"] for r in panel["invalid_quotes"]}
    assert not any(invalid.values())
    return {"binary":binary_report,"pair_results":details,
            "totals":{"binary_calls":2*len(binary),
                "binary_supported_correct":sum(sum(x>0 for x in r["margins"]) for r in binary_report.values() if r["gold"]),
                "binary_foil_correct":sum(sum(x<0 for x in r["margins"]) for r in binary_report.values() if not r["gold"]),
                "binary_claims_stably_correct":sum(r["stable"]==r["gold"] for r in binary_report.values()),
                "binary_averaged_labels_correct":sum(
                    (r["average"]>0 if r["average"]!=0 else None)==r["gold"] for r in binary_report.values()),
                "rank_bootstrap_correct":sum(r["separately_judged_rank_correct"] for r in details.values()),
                "contrast_calls":2*len(details),
                "contrast_correct_calls":sum(sum(m>0 for m in r["contrast_margins"]) for r in details.values()),
                "contrast_pairs_stably_correct":sum(r["contrast_stably_correct"] for r in details.values()),
                "contrast_order_disagreements":sum(r["contrast_order_disagrees"] for r in details.values()),
                "invalid_quotes_rejected":len(invalid)}}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("model",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    base.suite=suite
    base.score=score
    base.main(a.model,a.output)
    (a.output/"reserve-lock.json").write_text(serialize(
        {p.name:sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),RESERVE)})+"\n")
