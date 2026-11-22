"""Replay the semantic stress observations through the registered scorer."""
import json

import stress


def run():
    plan = stress.locked()
    base = stress.base
    fixture = base.fixture
    verified = json.loads((stress.HERE/"verified.json").read_text())["outputs"]
    parent = json.loads((stress.PARENT/"scores.json").read_text())
    records,_ = fixture.cases()
    output = {}
    for mode in stress.MODES:
        details, decisions, overlaps = {}, {}, {}
        for truth in (0,1):
            observed = []
            for order in base.MAPPINGS:
                name=f"{mode}/{truth}/{order}"
                request=next(p for p in plan["requests"] if p["id"]==name)
                label, scores = verified[name]["label"], verified[name]["logits"]
                mapping = base.MAPPINGS[order]
                raw = mapping[("A","B").index(label)]
                semantic_margin = scores[("A","B")[mapping.index(0)]]-scores[("A","B")[mapping.index(1)]]
                lexical, values = stress.scorer.lexical(request)
                observed.append({"order":order,"raw":raw,"margin":semantic_margin,
                                 "lexical":mapping[lexical],"overlap":values})
            margin = sum(row["margin"] for row in observed)/2
            decisions[truth] = int(margin<0)
            overlaps[truth] = observed[0]["lexical"]
            details[truth] = {"orders":observed,"mean_margin":margin,
                              "correct":decisions[truth]==truth}
        rows = []
        for q in fixture.RATES:
            for p in fixture.PRIORS:
                blind = parent["absent"]["action"]
                controls = {"paired":decisions,"lexical":overlaps,
                            "arrival":{i:parent["arrival_only"]["action"] for i in (0,1)},
                            "ceiling":{i:i for i in (0,1)}}
                score={key:float(fixture.receipt_value(records,q,p,acts|{None:blind}))
                       for key,acts in controls.items()}
                reference=fixture.evaluate(records,q,p)
                assert score["ceiling"] == reference["content_ceiling"] and score["paired"] <= score["ceiling"]
                rows.append({"delivery":float(q),"prior":float(p),"scores":score})
        output[mode] = {"observations":details,"deployment":rows,
                        "raw_correct":sum(r["raw"]==truth for truth,c in details.items() for r in c["orders"]),
                        "paired_correct":sum(d==truth for truth,d in decisions.items()),
                        "lexical_correct":sum(d==truth for truth,d in overlaps.items())}
    return output


if __name__=="__main__":
    print(json.dumps(run(),indent=2))
