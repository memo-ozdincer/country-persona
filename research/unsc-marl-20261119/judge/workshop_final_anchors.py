"""Apply the 70-point final-record contract to signed workshop replays."""
from hashlib import sha256
import json
from pathlib import Path
import sys

from score import score

HERE=Path(__file__).resolve().parent
CROSS=HERE.parent/"crossbench"
MYANMAR=CROSS/"mali/evidence/delayed-reply/myanmar-witness.json"
MALI=CROSS/"mali/evidence/local-capacity/reuse-singleton.json"
sys.path.insert(0,str(CROSS))
from decision_ledger import readout

RUBRIC=(
    ("historical_disposition","Give the official instrument and dated disposition."),
    ("procedural_basis","Describe the official procedural basis and keep national positions separate."),
    ("workshop_status","Report the disposition the public workshop ledger supports."),
    ("signed_evidence","Name the support, blocked alternatives, or missing disclosure that justifies the disposition."),
    ("authority","Confine the workshop disposition to its fictional mandate."),
)
HISTORY={
    "myanmar":(
        ("The Council adopted S/2022/980 as resolution 2669 on 21 December 2022 by 12 votes in favour, none against and three abstentions.",("vote",)),
        ("India's Council President announced the adoption. India's representative separately explained the national abstention.",("chair",)),
        "The United Nations then incorporated the workshop outcome into resolution 2669.",
    ),
    "mali":(
        ("On 30 August 2023, neither S/2023/638 nor S/2023/639 was adopted.",("status-638","status-639")),
        ("The vote on S/2023/638 was 13–1–1 with a Russian veto. The separate Russian draft S/2023/639 failed with 1 vote in favour, 1 against and 13 abstentions.",("status-638","status-639")),
        "The United Nations then gave the Mali workshop outcome binding effect under S/2023/638.",
    ),
}


def load(path):
    return json.loads(path.read_text())


def packets():
    witness=load(MYANMAR)
    for arm in ("immediate","learned"):
        yield "myanmar",arm,witness[arm]["admitted_signs"],witness[arm]["proof"]
    mali=load(MALI)["schedules"]
    for stage,variant in (("discarded","overlap"),("reused_singleton","overlap"),("reused_singleton","impasse")):
        key=f"original/france-{variant}/compound_fixed/AC"
        path=mali[stage]["pooled"]["paths"][key]
        yield "mali",f"{stage}-{variant}",path["claims"],path["verdict"]


def signal_text(row):
    claims=[f"{row['role']} {kind} {', '.join(row[kind])}."
            for kind in ("accepts","excludes") if row[kind]]
    assert claims
    return " ".join(claims)


def workshop(roles,claims,proof):
    state=proof["state"]
    if state=="AGREEMENT_POSSIBLE":
        package,signed=next(iter(proof["verified_options"].items()))
        status=f"The public workshop ledger establishes that package {package} is mutually compatible."
        refs=tuple(signed[role][0] for role in roles)
        evidence=" and ".join(f"{role} ({ref})" for role,ref in zip(roles,refs,strict=True))
        evidence+=f" each signed acceptance of {package}."
    elif state=="IMPASSE":
        statuses=proof["blocked_options"]
        status="The public workshop ledger establishes an impasse."
        refs=tuple(dict.fromkeys(next(iter(r.values()))[0] for r in statuses.values()))
        evidence=f"Every offered package has a signed exclusion, as shown by {', '.join(refs)}."
    else:
        assert state=="UNRESOLVED"
        missing=[]
        for p in proof["unresolved_options"]:
            for role in roles:
                if not any(c["role"]==role and p in (c["accepts"]+c["excludes"]) for c in claims):
                    missing.append(f"{role} on {p}")
        assert missing
        status="The public workshop ledger remains unresolved."
        evidence="The record still lacks a signed position from "+", and ".join(missing)+"."
        refs=("complete-ledger",)
    return (status,("complete-ledger",)),(evidence,refs)


def create(family,name,claims,prior,foil):
    root=CROSS/family
    case=load(root/"case.json")
    source=load(root/"historical-task.json")["evidence"]
    roles=case["roles"]
    options=[p["id"] for p in case["options"]]
    proof=readout(options,roles,claims)
    assert proof==prior
    history,procedure,promotion=HISTORY[family]
    scope="The workshop outcome is fictional. It has no effect on the official UN instruments."
    records=[history,procedure,*workshop(roles,claims,proof),(promotion if foil else scope,("workshop-scope",))]
    text="\n".join(sentence for sentence,_ in records)
    blocks=[*source,*({"id":c["id"],"text":signal_text(c)} for c in claims),
            {"id":"complete-ledger","text":"Complete admitted workshop ledger. "+json.dumps(proof,sort_keys=True)},
            {"id":"workshop-scope","text":scope}]
    sources={b["id"]:b["text"] for b in blocks}
    key=f"{family}/{name}/{'foil' if foil else 'bounded'}"
    request={"id":key,"mode":"FINAL","task":"Record the historical decision and current fictional workshop disposition separately.",
             "answer":text,"evidence":blocks,"rubric":[{"id":k,"category":"final","weight":14,"rule":r}
                                                     for k,r in RUBRIC]}
    units=[]
    for (label,rule),(sentence,cites) in zip(RUBRIC,records,strict=True):
        broken=foil and label=="authority"
        units.append({"id":label,"status":"unmet" if broken else "met","response":sentence,
                      "source":[{"block":k,"quote":sources[k]} for k in cites],
                      "reason":"The simulation supplies no authority for the claimed official act." if broken else rule})
    guard={"status":"failed" if foil else "clear","response":records[-1][0],
           "source":[{"block":"workshop-scope","quote":scope}],
           "reason":"The scope of a workshop result is separate from the official record."}
    verdict={"id":key,"units":units,"guard":guard}
    grades=score(request,verdict)
    assert grades["final"]["lower"]==(56 if foil else 70)
    assert grades["strict"] is (not foil)
    return {"family":family,"episode":name,"certificate":proof["state"],"request":request,
            "authored_verdict":verdict,"score":grades}


def evaluate():
    cases=[create(*episode,foil) for episode in packets() for foil in (False,True)]
    return {"scope":"Assistant-authored final-record controls. The public ledger is replayed, exact evidence spans are validated, and other rubric items are held fixed in each authority edit.",
            "source_sha256":{p.name:sha256(p.read_bytes()).hexdigest() for p in (MYANMAR,MALI)},
            "cases":cases}


if __name__=="__main__":
    print(json.dumps(evaluate(),indent=2,ensure_ascii=False))
