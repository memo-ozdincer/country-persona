"""Encode the single reading of opaque tribunal briefs against frozen criteria."""
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
ATTR={
    "1099b07cf7d300c4":("per-unity",),
    "27b86cebc988f247":("per-unity","srb-release","capacity"),
    "3a157d24c36541e7":("per-unity","rus-staffing","contrast"),
    "55616e06bd21ee45":("per-cooperation","srb-cooperation"),
    "74468285f36d469f":("per-unity","rus-staffing","contrast"),
    "7a1b237a71b81551":("per-unity","rus-medical"),
    "9f56a957b5242022":("per-cooperation","rus-medical"),
    "b4c9d4ec3fb424e8":("per-cooperation","srb-cooperation"),
    "b6cf917c4b92999f":("per-unity","srb-cooperation"),
    "b8ed0685bb81db73":("per-cooperation","rus-staffing"),
    "fc453b37d4d8b296":("per-unity","srb-cooperation"),
    "fc4db9d4b3db3db1":("per-cooperation",),
    "fd419bfbe99e682f":("per-cooperation","rus-staffing"),
}
COOP_SCOPE_UNCERTAIN={"55616e06bd21ee45","9f56a957b5242022","b8ed0685bb81db73"}
ATTR_SPANS={
    "per-unity":r"urged (?:the Council to (?:stay|remain) united|(?:Council )?unity|unity)[^.]*\.",
    "per-cooperation":r"(?:ability to combat impunity|combating impunity)[^.]*\.",
    "rus-staffing":r"earlier warnings [^.]*\.",
    "rus-medical":r"questioned the adequacy of Ratko Mladić.s medical care[^.]*Russian guarantees\.",
    "srb-cooperation":r"(?:Confirmed meeting cooperation obligations|Stated it meets cooperation obligations)[^.]*\.",
    "srb-release":r"Objected that the Mechanism had refused[^.]*guarantees from the Serbian Government\.",
    "capacity":r"Serbia \(participated without voting\)\..*?guarantees from the Serbian Government\.",
    "contrast":r"\*\*Attributed Positions:?\*\*.*?(?=\*\*Limitations)",
}


def match(pattern,text):
    result=re.search(pattern,text,flags=re.IGNORECASE|re.DOTALL)
    assert result, (pattern,text)
    return result.group().strip()


def grade(packet):
    ident=packet["id"]
    short=ident.removeprefix("final-")
    text=packet["answer"]
    source={row["id"]:row["text"] for row in packet["evidence"]}

    def bind(*names):
        return [{"block":name,"quote":source[name]} for name in names]

    reviewed={}
    start=min(text.index("Chapter VII"),text.index("Serge Brammertz"))
    end=max(text.index("Chapter VII")+len("Chapter VII"),text.index("30 June 2020")+len("30 June 2020"))
    uncertain=short=="fd419bfbe99e682f"
    reviewed["action"]={"status":"uncertain" if uncertain else "met","response":text[start:end],
                        "source":bind("action"),"reason":"Chapter VII may modify the cooperation statement."
                        if uncertain else "The span preserves the appointment, authority and dates."}
    p=r"underlined [^\n]*full state cooperation"
    left=re.search(p,text,re.IGNORECASE).start()
    right=re.search(r"conclusion of (?:its|the|the Mechanism's) progress review",text,re.IGNORECASE).end()
    reviewed["review"]={"status":"met","response":text[left:right],"source":bind("action"),
                        "reason":"Records both cooperation and the conclusion of the progress review."}

    for name in ATTR[short]:
        groups={"contrast":("per-unity","rus-staffing"),"capacity":("vote","srb-release")}
        reviewed[name]={"status":"met","response":match(ATTR_SPANS[name],text),
                        "source":bind(*groups.get(name,(name,))),
                        "reason":"The cited statement preserves the corresponding attributed position or contrast."}

    roster=re.search(r"\*\*Voting Members:\*\* 14 \(Peru, (?:France|Russia, Serbia)[^\n]*",text)
    if roster:
        guard={"status":"failed","source":bind("vote"),"response":roster.group(),
               "reason":"The supplied vote record provides the tally and the capacities of Russia and Serbia. It does not support this named roster."}
    elif short in COOP_SCOPE_UNCERTAIN:
        marker=match(r"underlined[^\n.]*full state cooperation[^\n.]*\.",text)
        guard={"status":"uncertain","source":bind("action","per-cooperation"),"response":marker,
               "reason":"The wording may treat Peru's specific enforcement examples as the Council's operative instruction."}
    else:
        guard={"status":"clear","source":[],"response":"","reason":"No material unsupported assertion was found."}
    missing={"status":"unmet","source":[],"response":"","reason":"The full required attributed detail is missing."}
    return {"id":ident,"units":[{"id":row["id"]} | reviewed.get(row["id"],missing)
                               for row in packet["rubric"]],"guard":guard}


def run():
    cards=json.loads((HERE/"packets.json").read_text())
    before=json.loads((HERE.parent/"historical-source-messages/verdicts.json").read_text())
    return {ident:before[ident] if ident in before else grade(packet) for ident,packet in cards.items()}


if __name__=="__main__":
    print(json.dumps(run(),ensure_ascii=False,indent=2))
