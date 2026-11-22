"""Replay a matched final-record pair that differs in the scope of the report."""
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/"judge"))
from score import score

SENTENCES=(
    ("The Council adopted S/2022/980 as resolution 2669 (2022).",("vote",)),
    ("The vote was 12–0–3, with China, India and Russia abstaining.",("vote",)),
    ("The United Kingdom sponsored and supported the text after regional consultations, citing the need to end violence and enable access.",("uk","vote")),
    ("India abstained and advocated quiet, constructive diplomacy in view of neighboring countries' concerns.",("india","vote")),
    ("India's representative announced adoption as Council President and later explained the abstention in a national capacity.",("chair",)),
    ("The resolution demanded an end to violence and called for humanitarian access.",("mandate",)),
    ("It acknowledged ASEAN's central role and called for coordination with the UN.",("mandate",)),
    ("Both delegations drew attention to ASEAN and neighboring countries, while differing on how the Council should act.",("uk","india")),
    ("The Secretary-General or his Special Envoy, coordinating with the ASEAN Special Envoy, was asked to report orally to the Council by 15 March 2023 on support for the Five-Point Consensus.",("mandate",)),
    ("The adopted reporting instruction was an oral briefing to the Council.",("mandate",)),
)
FALSE="The resolution also imposed a mandatory public aggregate report."


def build():
    packet=json.loads((HERE/"historical-task.json").read_text())
    sources={d["id"]:d["text"] for d in packet["evidence"]}
    output=[]
    for fault in (False,True):
        answer=" ".join(t for t,_ in SENTENCES)+(f" {FALSE}" if fault else "")
        request={**packet,"answer":answer,"id":"myanmar-"+("foil" if fault else "correct")}
        units=[]
        for item,(sent,keys) in zip(packet["rubric"],SENTENCES,strict=True):
            broken=fault and item["id"]=="authority"
            units.append({"id":item["id"],"status":"unmet" if broken else "met","response":FALSE if broken else sent,
                          "source":[{"block":k,"quote":sources[k]} for k in keys],
                          "reason":"It attributes an extra reporting requirement to the adopted text." if broken else item["rule"]})
        guard={"status":"failed" if fault else "clear","response":FALSE if fault else SENTENCES[-1][0],
               "source":[{"block":"mandate","quote":sources["mandate"]}] if fault else [],
               "reason":"The official reporting requirement is oral and directed to the Council."}
        verdict={"id":request["id"],"guard":guard,"units":units}
        scorecard=score(request,verdict)
        assert scorecard["final"]["lower"]==(63 if fault else 70) and scorecard["strict"]!=fault
        output.append({"request":request,"verdict":verdict,"score":scorecard})
    return {"scope":"Assistant-authored fixtures. Exact source and candidate span validation, no model judge calls.","anchors":output}


if __name__=="__main__":
    print(json.dumps(build(),ensure_ascii=False,indent=2))
