"""Keep four byte-identical source targets, add one complete application target.

WPS remains an exposed monitor. A Brazil/Libya source-family/country control is
frozen before fitting. All choices are supplied: this tests faithful realization.
"""
import copy
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PARENT=ROOT/"research/native-plan-writer-20261019-v1"
CONTROL=ROOT/"research/native-plan-writer-application-20261019-v1"
OUT=ROOT/"research/native-application-writer-20261019-v1"

Q=("Hypothetical workshop implementation plan Q for resolution 2664 funds timely basic-needs aid through the specified organizations, "
   "retains ordinary eligibility checks and a monthly diversion review, but contains no defined proactive 1267 Monitoring Team role or standardized reporting to that Team.")
Q_PLAN=("For this exercise, preserve Q's timely aid, eligibility checks and existing monthly review; add the missing proactive Team role and standardized reporting. "
        "Provide a Team liaison receiving standardized diversion reports and a staffed, risk-prioritized verification/reporting workflow alongside delivery. "
        "Reporting consumes staff and can slow aid; use proportionate triage rather than a new per-delivery approval veto. "
        "These are analytical recommendations, not an observed Indian endorsement of Q or an established future vote.")
APPLICATION=("For this workshop exercise, Q already funds timely aid through specified organizations, retains eligibility checks and a monthly diversion review, "
             "but lacks a defined proactive Team role and standardized reporting. I recommend a Team liaison receiving standardized diversion reports and a staffed, "
             "risk-prioritized verification/reporting workflow alongside delivery. Reporting needs staff and can slow aid; proportionate triage preserves access without "
             "a new per-delivery veto. These are analytical recommendations. Indian endorsement of Q or an unspecified future text, and any future vote, "
             "remain unestablished by the supplied record.")

BRA_POINTS=[
    ("complementarity","National jurisdictions have the primary duty; ICC acts only when the State is unable or unwilling.",["primary duty of States","unable or unwilling"]),
    ("legal_scope","Nonparties have no Rome Statute obligations, yet resolution1970 under ChapterVII requires Libyan authorities to cooperate fully.",["States that are not parties to the Rome Statute have no obligation under the Statute","under Chapter VII","Libyan authorities should cooperate fully"]),
    ("cooperation","Other States/organizations are urged to cooperate; ICC has no enforcement instruments and depends on States; requests must conform to Statute/relevant Council resolutions.",["urged all States","no enforcement instruments","fully consistent with the Rome Statute"]),
    ("positive","Brazil welcomes strengthened OTP-Libyan cooperation and its more positive trajectory.",["strengthen its cooperation with the Libyan national authorities","more positive trajectory"]),
    ("victims","Empower victims/witnesses/affected communities inside AND outside Libya; further engage victims and their representatives.",["victims, witnesses and the communities affected, both inside and outside Libya","further engage with victims and their representatives"]),
    ("equality","Justice must avoid politicization, selectivity/double standards; all serious-crime victims treated equally regardless of situation.",["not by politicization","all victims of the most serious crimes must be treated equally"]),
    ("status","No ICC judgments in the Libyan situation so far; evidence collection/investigative progress is welcomed, not a conviction or completed ICC adjudication.",["no judgments have been brought in the Libyan situation so far","progress that has been made in the investigations"]),
    ("transparency","Ask for additional information on the four key lines of inquiry.",["additional information regarding his four key lines of inquiry"]),
    ("hope","Retain Brazil's real hope for fruitful OTP-Libyan relations and complementarity-based justice/accountability.",["in accordance with the principle of complementarity","hope that a fruitful relationship"]),
]
FRA_POINTS=[
    ("support","France supports Court/Rome Statute integrity, condemns cyberattack, and has real continuing political/operational/human/financial support.",["France condemns the recent cyberattack","political, operational, human and financial support"]),
    ("inquiries","Four lines progress;2014–2020 operations inquiry is nearing completion, not all proceedings complete.",["four main lines of investigation","nearing completion"]),
    ("roadmap","Next report may present a potential completion roadmap under1970; not a completed roadmap or final judgments.",["next report a potential road map"]),
    ("national","National arrests/prosecutions of migrant-crime suspects reflect cooperation and OTP evidence; not ICC convictions.",["by the competent national authorities","information, evidence and guidelines"]),
    ("office","Joint-team missions and progress toward a Tripoli liaison office in2024; not already open.",["progress made towards establishing a liaison","office for the Prosecutor in Tripoli in 2024"]),
    ("engagement","Victim/witness/community engagement and civil-society documentation-guideline exchanges should intensify.",["engage more closely with victims, witnesses","intensification of exchanges"]),
    ("scope","Investigate/prosecute all serious Libya crimes since2011, including Daesh and migrant/refugee crimes; international/UN support vital.",["most serious crimes committed in Libya since 2011","including crimes committed by Da’esh"]),
    ("libya","Support sovereign,united,stable,democratic Libya and regional stability.",["sovereign, united, stable and democratic Libya"]),
]
R=("Hypothetical follow-up workplan R emphasizes cooperation with Libyan authorities and a generic public progress update. "
   "It provides no channel for victims or witnesses outside Libya and requests no detail on the four key lines of inquiry.")
R_PLAN=("For this workshop exercise, preserve R's cooperation and public update, add a protected two-way channel accessible to victims/witnesses and their representatives "
        "inside and outside Libya, and request a line-by-line progress update on the four inquiries. Expanded outreach/reporting requires staff and witness-privacy "
        "safeguards; narrower outreach costs less but risks selectivity. Recommendations are analytical, not an observed Brazilian endorsement of R or a future vote. "
        "Preserve the existing legal qualifications and no-judgments/investigative-progress distinction.")
APP_UNITS={
    "A1":"Accurately acknowledge what the current hypothetical plan already provides and the stated remaining gaps; do not invent a removed defect.",
    "A2":"Give both supplied concrete operational directions, addressing the current gaps rather than unrelated stock examples.",
    "A3":"Explain the supplied practical competing resource/timing/privacy cost; generic balance or correct action words alone do not suffice.",
    "A4":"Label the recommendation as exercise analysis, not an observed national commitment; official endorsement of this plan/future vote remains unestablished while real ongoing positions/hope remain."
}


def build():
    old=json.loads((PARENT/"examples.json").read_text())
    source=[copy.deepcopy(r) for r in old if r["split"] in {"train","eval"}]
    for row in source:
        if row["split"]=="eval":row["split"]="source_eval"
    controls=json.loads((CONTROL/"examples.json").read_text())
    old_rubric=json.loads((CONTROL/"rubric.json").read_text())
    coverage=json.loads((CONTROL/"coverage-addendum.json").read_text())
    apps=[]
    for r in controls:
        apps.append({**copy.deepcopy(r),"episode":"8514","split":"application_eval","target":None,
                     "source_map_units":copy.deepcopy(coverage["source_units"][r["id"]])})
    ind=copy.deepcopy(next(r for r in source if r["id"]=="9214-IND"))
    common,role=ind["messages"][1]["content"].split("\nREQUESTED ROLE:")
    ind.update(id="application-9214-IND",split="train",messages=[copy.deepcopy(controls[0]["messages"][0]),
        dict(role="user",content=common+"\nHYPOTHETICAL APPLICATION Q\n"+Q+"\nPROVIDED ANALYTICAL PLAN\n"+Q_PLAN+"\nREQUESTED ROLE:"+role)],
        target=ind["target"].split("Neither our constructive engagement",1)[0].rstrip()+"\n\n"+APPLICATION,
        units={**ind["units"],**APP_UNITS})
    text_path=ROOT/"data/raw/compression-libya-grounding-20261006-v1/record-9469.txt"
    text=text_path.read_text(); bodies={};spans=[];mapped={}
    for c,begin,end,entries in [("BRA","Mr. França Danese (Brazil):","Mr. Pérez Loose (Ecuador)",BRA_POINTS),
                                ("FRA","Mrs. Dime Labille (France)","Mr. Fernandes (Mozambique)",FRA_POINTS)]:
        start=text.index(begin);stop=text.index(end,start);body=text[start:stop].rstrip();bodies[c]=body
        points=[]
        for key,claim,anchors in entries:
            support=[]
            for anchor in anchors:
                a=body.index(anchor);support.append(dict(start=start+a,end=start+a+len(anchor),quote=anchor))
            points.append(dict(id=key,claim=claim,support=support))
        mapped[c]=points
        spans.append(dict(country=c,path=str(text_path.relative_to(ROOT)),start=start,end=start+len(body),body=body,
                          body_sha256=hashlib.sha256(body.encode()).hexdigest(),points=points))
    context=("SCENARIO\nUN Security Council; 8 November 2023; S/PV.9469, The situation in Libya; national statements after briefing on the ICC's 26th report. "
             "No subsequent vote or government instruction is supplied. These are dated public institutional positions, not population beliefs.\n\nCOMPLETE COUNTRY SOURCES\n")
    for c in ["BRA","FRA"]:context+="\n[9469-"+c+"]\n"+bodies[c]+"\n"
    context+="\nCHECKED FACT MAP (same-assistant source paraphrases; independent review pending)\n"
    for c in ["BRA","FRA"]:
        context+="\n"+c+" | national delegation |2023-11-08\n"+"\n".join("- "+p["id"]+": "+p["claim"] for p in mapped[c])+"\n"
    context+="\nHYPOTHETICAL APPLICATION R\n"+R+"\nPROVIDED ANALYTICAL PLAN\n"+R_PLAN+"\nREQUESTED ROLE: BRA national delegation."
    brazil=dict(id="application-9469-BRA",country="BRA",episode="9469",split="new_eval",target=None,
        messages=[copy.deepcopy(controls[0]["messages"][0]),dict(role="user",content=context)],
        units={**{p["id"]:p["claim"] for p in mapped["BRA"]},**APP_UNITS})
    rows=[r for r in source if r["split"]=="train"]+[ind]+[r for r in source if r["split"]=="source_eval"]+apps+[brazil]
    assert len(rows)==10 and sum(r["split"]=="train" for r in rows)==5
    for r in rows:
        if r["target"] is not None:assert len(r["target"].split())<=240
    for r in old:
        if r["split"]=="train":
            actual=next(x for x in rows if x["id"]==r["id"])
            assert actual["messages"]==r["messages"] and actual["target"]==r["target"] and actual["units"]==r["units"]
    return rows,dict(new_source_spans=spans,old_examples_sha256=hashlib.sha256((PARENT/"examples.json").read_bytes()).hexdigest(),
        corrected_application_examples_sha256=hashlib.sha256((CONTROL/"examples.json").read_bytes()).hexdigest(),
        unchanged_four_source_targets_and_inputs=True,old_application_rubric=old_rubric,
        historical_scope="Libya is new to native32/native40 fitting and this application evaluation, but its document was historically used in older project branches. Not sealed OOD. WPS is an exposed adaptive monitor.")


if __name__=="__main__":
    if (OUT/"release.json").exists():raise ValueError("Frozen release exists")
    OUT.mkdir(exist_ok=True)
    rows,grounding=build()
    (OUT/"examples.json").write_text(json.dumps(rows,indent=2,ensure_ascii=False)+"\n")
    (OUT/"grounding.json").write_text(json.dumps(grounding,indent=2,ensure_ascii=False)+"\n")
    for r in rows:
        (OUT/(r["id"]+".txt")).write_text("\n\n".join(m["role"].upper()+"\n"+m["content"] for m in r["messages"])+("\n\nTRAINING TARGET\n"+r["target"] if r["target"] else "\n\nNO FITTING TARGET")+"\n")
    print(json.dumps([dict(id=r["id"],split=r["split"],units=len(r["units"]),target_words=len(r["target"].split()) if r["target"] else None) for r in rows]))
