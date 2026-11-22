"""Inspect fenced judge replies without altering their judgments or citations."""
import json
import re

import live


def run():
    rows=live.prior.report.load(live.OUT/"tokens.jsonl")
    modes=live.fixtures()
    cases=[]
    for row in rows:
        raw=row["reply"]["text"]
        match=re.fullmatch(r"```json\s*([\s\S]*?)\s*```",raw)
        if not match:
            continue
        category=row["mode"]
        packet, expected, *context=modes[category][row["id"]]
        targets={}
        try:
            verdict=live.suite.decode_verdict(row["reply"] | {"text":match.group(1)})
            proposed={item["id"]:item["points"] for item in verdict["ratings"]}
            targets={k:{"expected":v,"observed":proposed.get(k)} for k,v in expected.items()}
            live.e.process_score(*context,verdict)
            validity="valid"
        except (ValueError,KeyError,TypeError,AttributeError) as exc:
            validity=str(exc)
        cases.append({"id":row["id"],"mode":category,"validity":validity,"labels":targets})
    return cases


if __name__=="__main__":
    print(json.dumps(run(),indent=2))
