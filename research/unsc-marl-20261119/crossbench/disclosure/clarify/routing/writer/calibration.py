"""Fixed minimal pairs for public-evidence scope and rubric independence."""
import json

from review import packet,score
from run import suite


def build():
    row = next(r for r in suite() if r["id"]=="impasse-AC-script")
    history = ("History: S/2022/925 became resolution 2664 (2022) by 14–0–1. Brazil voted yes and India abstained. "
               "India said its request for proactive 1267 Monitoring Team involvement and robust reporting was not fully addressed.")
    good = "\n".join((history, "Workshop: UNRESOLVED",
                       "Evidence: Only F remains open. Brazil accepts it and India has made no admission on F.",
                       "Positions: India accepts A (claim-1); Brazil accepts F (claim-7).",
                       "Authority: These fictional workshop proposals do not amend the resolution or record new official decisions."))
    changed = {
        "correct":good,
        "unsupported-proof":good.replace("Workshop: UNRESOLVED","Workshop: IMPASSE").replace(
            "Only F remains open. Brazil accepts it and India has made no admission on F.",
            "Every package was excluded. India rejected F."),
        "invented-authority":good.replace("do not amend the resolution or record new official decisions",
                                         "amend the resolution with immediate effect"),
    }
    result = []
    for name, memo in changed.items():
        deck = packet({**row,"output":memo}, name)
        blocks = {item["id"]:item["text"] for item in deck["evidence"]}
        history_line, workshop, evidence, positions, authority = memo.splitlines()

        def citations(ids):
            return [{"block":k,"quote":blocks[k]} for k in ids]

        def unit(key, met, source, response, reason):
            return {"id":key,"status":"met" if met else "unmet",
                    "source":citations(source),"response":response,"reason":reason}

        valid_proof = name!="unsupported-proof"
        valid_authority = name!="invented-authority"
        answer = {"id":name,"units":[
            unit("disposition",valid_proof,["roll","public-proof"],history_line+"\n"+workshop,
                 "Historical record is intact; workshop line "+("matches the proof." if valid_proof else "overstates the proof.")),
            unit("operative",valid_proof,["claim-7","public-proof"],evidence,
                 "F is publicly unresolved and Brazil accepts it."),
            unit("positions",True,["claim-1","claim-7"],positions,"Both scoped acceptances match their claim IDs."),
            unit("unresolved",valid_proof,["india","public-proof"],history_line+"\n"+workshop+"\n"+evidence,
                 "The historical concern is correct; the status of the remaining option must also be preserved."),
            unit("authority",valid_authority,["scope"],authority,"No workshop statement changes the official resolution."),
        ],"guard":{"status":"clear" if valid_authority else "failed","source":citations(["scope"]),
                   "response":authority,"reason":"The authority line "+("respects the post-vote scope." if valid_authority else "invents an amendment.")}}
        result.append({"packet":deck,"verdict":answer,"score":score(deck,answer)})
    return result

if __name__=="__main__":
    print(json.dumps(build(),indent=2,ensure_ascii=False))
