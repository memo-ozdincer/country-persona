"""Convert explicit assistant annotations to validated exact-span verdicts."""
import argparse
import json
from pathlib import Path

from review import score


def annotate(record, declaration):
    lines = dict(line.split(": ",1) for line in record["answer"].splitlines() if ": " in line)
    blocks = {item["id"]:item["text"] for item in record["evidence"]}

    def citation(key):
        return {"block":key,"quote":blocks[key]}

    def span(order):
        if not order:
            return ""
        parts = [f"{name}: {lines[name]}" for name in order]
        start = record["answer"].index(parts[0])
        end = record["answer"].index(parts[-1],start)+len(parts[-1])
        return record["answer"][start:end]

    def expand(raw):
        status, lines, sources, reason = raw
        return {"status":status,"source":[citation(s) for s in sources],
                "response":span(lines),"reason":reason}

    result = {"id":record["id"],"units":[{"id":key,**expand(raw)}
              for key,raw in declaration.items() if key!="guard"],"guard":expand(declaration["guard"])}
    return result,score(record,result)


def report(deck, declarations):
    result = []
    for row in deck:
        packet = row["packet"]
        verdict, bounds = annotate(packet,declarations[packet["id"]])
        conditions = row["mechanics"]
        strict = (bounds["strict"] and conditions.get("ended",True) and all(conditions[k] for k in
                  ("headings","exact_disposition_line","word_limit_met")))
        result.append({"record":packet["id"],"model_id":row["model_id"],"mechanics":conditions,
                       "judge":bounds,"full_contract":strict,"verdict":verdict})
    return result


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("deck",type=Path)
    p.add_argument("declarations",type=Path)
    args=p.parse_args()
    print(json.dumps(report(json.loads(args.deck.read_text()),json.loads(args.declarations.read_text())),
                     indent=2,ensure_ascii=False))
