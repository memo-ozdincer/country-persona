"""Replay optional memo admission policies with a checked record fallback."""
from collections import Counter
import json
from pathlib import Path
import sys


def load(path):
    return json.loads(path.read_text())


def evaluate(folder):
    review=load(folder/"frozen-judge/metrics.json")
    thresholds=load(folder/"frozen-judge/thresholds.json")["midpoint_transfers"]
    references=load(folder/"reference-render.json")["records"]
    # Match the reference to the visible state, including each holder's card.
    fallbacks={}
    for record in references:
        family=record["id"].split("/")[0]
        cards=tuple(sorted((r["owner"],r["card"]) for r in record["workshop_fields"]))
        title=record["memo"].splitlines()[0]
        signature=(family,title,cards)
        if signature in fallbacks:
            assert record["memo"]==fallbacks[signature]["memo"]
        assert len(record["memo"].split())<=100
        fallbacks[signature]=record
    entries={}
    for source,path in (("original",folder),("retest",folder/"prompt-control")):
        key=load(path/"review-key.json")
        scores=load(path/"scores.json")["archive"]
        for raw in (json.loads(line) for line in (path/"memos.jsonl").read_text().splitlines()):
            if raw["id"]!=raw["inference_id"]:
                continue
            ident=f"{source}/{key[raw['id']]}"
            cards=tuple(sorted((r["owner"],r["card"]) for r in raw["expected"]["evidence_at_chair"]))
            title=f"Workshop status: {raw['expected']['checked_status']}"
            baseline=fallbacks[(raw["family"],title,cards)]
            assert baseline["historical_evidence"]==json.loads(raw["messages"][1]["content"])["historical_evidence"]
            judged=review["cases"][ident]
            observed=scores[raw["id"]]
            assert judged["expected"]==observed["guard"]
            entries[ident]={"family":raw["family"],"source_memo":raw["id"],"judgments":judged,
                            "format_ok":observed["word_cap_pass"] and observed["exact_line"],
                            "generated":raw["output"],"fallback":baseline["memo"]}
    strategies={
        "accept_all":lambda r:True,
        "stable_guard":lambda r:r["judgments"]["stable"]=="clear",
        "pooled_guard":lambda r:r["judgments"]["pooled"]=="clear",
        "other_family_midpoint":lambda r:sum(r["judgments"]["margins"])/2 <
            next(v["midpoint"] for f,v in thresholds.items() if f!=r["family"]),
        "pooled_and_format":lambda r:r["format_ok"] and r["judgments"]["pooled"]=="clear",
    }
    totals,records={},{}
    for method,allow in strategies.items():
        tally,rendered=Counter(),{}
        for ident,r in entries.items():
            accepted=allow(r)
            label=r["judgments"]["expected"]
            kind="accepted" if accepted else "fallback"
            tally[f"{kind}/{label}"]+=1
            if accepted and r["format_ok"]:
                tally["accepted/format_ok"]+=1
            rendered[ident]={"route":kind,"case":r["source_memo"],
                             "source_guard_label":label,"memo":r["generated" if accepted else "fallback"]}
        totals[method]=dict(tally)
        records[method]=rendered
    return {"scope":"Retrospective comparison on ten unique actual model memos. Same-assistant guard annotations measure errors. Fallback uses the existing case-specific reference renderer on matching evidence. Format and critical guard remain distinct.",
            "unique_memos":len(entries),"totals":totals,"records":records}


if __name__=="__main__":
    print(json.dumps(evaluate(Path(sys.argv[1])),indent=2,ensure_ascii=False))
