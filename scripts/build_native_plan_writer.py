"""Four complete, native-chat, source-conditioned country writing targets.

Sanctions/climate fit; WPS is excluded as a whole episode. All positions are
given, so this tests evidence-preserving realization, not preference discovery.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research/native-plan-writer-20261019-v1"
PRIOR = ROOT / "research/scenario-role-sft-20261017-v1"
WPS = ROOT / "data/prepared/synthesis-rehearsal-wps-20261006-v1/wps-statements.json"

SYSTEM = (
    "Write one coherent public statement for the requested dated national delegation, at most 240 words. "
    "This is an evidence-conditioned paraphrase exercise, not an authentic quotation or a prediction of the next speech. "
    "Preserve EVERY own-country point in the supplied checked fact map, including qualifications and ongoing commitments. "
    "Use the complete sources to resolve wording. Keep country, institution, recipient, object, polarity and event stage correct. "
    "Other delegations' distinctive policies are not your own. Shared principles can be shared. "
    "Distinguish an announced proposal, support, an adopted text and a recorded vote. "
    "An unspecified future text or future vote remains unestablished; that does not erase real ongoing commitments or known past votes. "
    "Do not invent events, official conditions, amounts or other speakers. Write only the requested statement, with no analysis or extra delegation turn."
)

# (Unit id, required meaning, literal navigation anchors in the FULL statement.)
POINTS = {
    "9214-GBR": [
        ("adoption", "Welcome adopted resolution 2664 (2022), congratulating US and Ireland.", ["congratulates the United States and Ireland"]),
        ("past_action", "UK sponsored the adopted resolution; this is a known past action.", ["voted in favour and to have been a sponsor"]),
        ("sanctions", "Sanctions remain a core Council tool under the Charter against peace/security threats.", ["Sanctions are a core part", "In line with the Charter"]),
        ("security", "Sanctions address weapons flows and terrorism, not an endorsement of ending sanctions.", ["stop weapons flows and tackle terrorism"]),
        ("scope", "Only specified organizations' necessary humanitarian/basic-needs activities do not violate UN asset freezes.", ["certain activities necessary for humanitarian assistance", "specified organizations"]),
        ("providers", "Clarity protects humanitarian providers AND their service providers.", ["humanitarian providers and their service providers"]),
        ("benefit", "The purpose is more effective aid delivery to vulnerable people/save lives.", ["getting aid to those in need more effectively"]),
    ],
    "9214-IND": [
        ("provisional", "Article 41 sanctions are provisional, not an end in themselves.", ["under Article 41", "provisional in nature and not permanent"]),
        ("civilian_trade", "Intended effects must avoid worsening civilian suffering and harming legitimate trade/regional partners.", ["do not further exacerbate the suffering", "legitimate trade and economic activities"]),
        ("constructive", "India engaged constructively in negotiations on resolution 2664.", ["India engaged constructively"]),
        ("carveout", "Carveout supports timely humanitarian/basic-needs delivery and agency predictability/safeguards.", ["timely delivery of humanitarian assistance", "predictability and safeguards"]),
        ("risk", "1267-listed groups in state-supported terrorist havens may exploit humanitarian exceptions; caution/due diligence required.", ["regime established pursuant to resolution 1267", "with full State hospitality"]),
        ("fronts", "Groups masquerade as humanitarian/civil society organizations to evade sanctions, raise funds and recruit fighters.", ["reincarnating themselves as humanitarian organizations", "raise funds and recruit fighters"]),
        ("political", "Exemptions must not mainstream terrorist entities politically.", ["mainstreaming of terror entities in the political space"]),
        ("monitor", "India sought proactive 1267 Monitoring Team and robust reporting; final text did not fully address these concerns; hopes for future correction.", ["a proactive role for the 1267 Monitoring Team", "not fully addressed in the final text", "shortcoming will be corrected in the future"]),
    ],
    "8923-IND": [
        ("g5", "Support G-5 Sahel Joint Force with adequate sustainable resources, training/logistics because current support is inadequate.", ["current model of support to the Joint Force is inadequate", "adequate and sustainable resources"]),
        ("climate_real", "Climate change is a defining challenge and can exacerbate conflicts; rejecting Council track is not denying climate action.", ["one of the defining challenges", "exacerbated conflicts in many places"]),
        ("forum", "Oppose separate Council climate/security track; retain holistic UNFCCC consensus with all developing countries participating.", ["not think that it is appropriate to draw a separate link", "consensus-driven template", "all developing countries participating"]),
        ("causality", "Climate-only explanations oversimplify conflict; climate does not justify terrorism.", ["viewing conflicts only through the prism of climate change", "neither can it justify terrorist acts"]),
        ("commitment", "Keep real Paris/Glasgow commitments including net zero by 2070.", ["firmly committed to achieving the outcome of COP26", "net zero by the year 2070"]),
        ("finance", "Developed countries must meet equitable mitigation/adaptation finance and technology-transfer duties; India urges $1 trillion financing early.", ["climate finance and technology transfer", "both mitigation and adaptation", "$1 trillion at the earliest"]),
        ("capacity", "India remains willing to extend capacity-building assistance to affected countries' armed forces against terrorism.", ["willing to extend and expand its capacity-building assistance"]),
    ],
    "8923-GBR": [
        ("multiplier", "Climate is a threat multiplier for fragile/conflict-affected states, not the sole cause of terrorism.", ["multiplier of the threats already facing vulnerable populations"]),
        ("example", "Sahel rainfall changes fuel farmer/herder conflict and can enable violent extremism.", ["changes in rainfall have fuelled conflict between farmer and herder"]),
        ("glasgow", "Glasgow keeps 1.5 degrees hope alive, with net-zero/deforestation commitments.", ["hope of limiting the rise in global temperature to 1.5", "net zero, ending and reversing deforestation"]),
        ("finance", "Double adaptation financing and meet $100 billion goal by 2023 at latest.", ["doubling of adaptation financing", "$100 billion goal by 2023 at the latest"]),
        ("reporting", "Support comprehensive UN reporting on climate-security links and CTED examining terrorism's conditions.", ["report comprehensively on the links between climate and security", "Counter-Terrorism Committee Executive Directorate"]),
        ("council", "All UN parts including Council have a role; UK explicitly supports the submitted draft.", ["including the Security Council, have a critical role", "we support the draft resolution submitted"]),
        ("participation", "Women and girls must participate meaningfully in an inclusive approach, not just receive protection.", ["fully inclusive approach", "they can play a meaningful role"]),
    ],
    "8514-FRA": [
        ("adoption", "France welcomes adopted German-initiated resolution 2467 (2019), a milestone rather than the end of the effort.", ["France welcomes the adoption of resolution 2467", "not the end of our journey"]),
        ("mandate", "Preserve strengthened Patten/Special Representative mandate and survivor-centred approach.", ["strengthening the mandate", "approach focused on the survivors"]),
        ("children", "Preserve requested Secretary-General report on children born of rape by 2021 (a request, not a completed report).", ["by 2021", "report on children born out of rape"]),
        ("omission", "Criticize removal of previously agreed SRH language under permanent-member/veto pressure despite welcoming adoption.", ["under pressure from several permanent members", "removal of the reference to sexual and reproductive health"]),
        ("need", "Victims need sexual/reproductive health care; omission undermines women's dignity.", ["The victims clearly need that care", "undermines the dignity of women"]),
        ("autonomy", "Women decide freely about bodies, including choosing to terminate involuntary pregnancies.", ["right to decide to terminate their pregnancies", "make decisions freely about their own bodies"]),
        ("ongoing", "France will keep promoting full SRH care/rights in every context, Council, other UN bodies and elsewhere.", ["in every context", "continue to support and promote", "other United Nations bodies and elsewhere"]),
        ("framework", "Earlier WPS health provisions 2106 paragraph19 and1889 paragraph10 remain in reaffirmed framework; omission does not erase them.", ["constitute the framework for our collective action", "paragraph 19 of resolution 2106", "paragraph 10 of resolution 1889"]),
    ],
    "8514-GBR": [
        ("adoption", "UK welcomes German-achieved adoption of resolution 2467 (2019) despite defects.", ["congratulations to Germany", "successful outcome to resolution 2467"]),
        ("survivors", "Preserve survivor-centred approach as a national priority.", ["recognition of the survivor-centred approach"]),
        ("justice", "More steps are still required for true justice/accountability.", ["more steps need to be taken to achieve true justice and accountability"]),
        ("disproportionate", "Conflict-related sexual violence disproportionately affects women and girls.", ["disproportionate impact on women and girls"]),
        ("civil_society", "Civil society has an important role.", ["important role that civil society plays"]),
        ("omission", "Regret omitted survivor-service language; acute need for comprehensive reproductive/sexual health care.", ["deeply regret the language on services", "comprehensive reproductive and sexual health care"]),
        ("ongoing", "Keep real continuing UK support for survivor access to SRH care around the world.", ["United Kingdom will continue to support access", "around the world"]),
        ("compatibility", "Care access is essential/compatible with survivor-centred approach; do not reverse that relationship or pool France's explicit termination statement into UK source.", ["If we are to have a survivor-centred approach, we cannot ignore"]),
    ],
}

TARGETS = {
    "9214-GBR": """The United Kingdom welcomes the Council's adoption of resolution 2664 (2022) on 9 December and congratulates the United States and Ireland. We sponsored the resolution and voted in favour. Sanctions remain a core Council tool under the UN Charter for addressing threats to peace and security, stopping weapons flows and tackling terrorism.

The humanitarian carveout does not end sanctions. It clarifies that specified organizations' activities necessary for humanitarian assistance or basic human needs do not violate UN asset freezes. That clarity matters for humanitarian providers and their service providers, helping aid reach vulnerable people more effectively and saving lives. Our support for this adopted resolution and our recorded favourable vote are established facts. They do not establish our endorsement of an unspecified future text or any future vote.""",
    "9214-IND": """India abstained on resolution 2664 (2022), while engaging constructively in its negotiations. Article 41 sanctions are provisional, not an end in themselves. Their implementation must avoid worsening civilian suffering and must consider legitimate trade and regional partners. The humanitarian carveout supports timely assistance and basic human needs while offering agencies predictability and safeguards.

Our concerns centre on exploitation by 1267-listed groups enjoying state hospitality in terrorist havens. Groups masquerading as humanitarian or civil-society organizations can evade sanctions, raise funds and recruit fighters. Exemptions must not enable their political mainstreaming. Due diligence and extreme caution are essential.

We sought a proactive role for the 1267 Monitoring Team and robust reporting. Those concerns were not fully addressed in the adopted text. We hope implementation reviews and Monitoring Team feedback will permit correction. Neither our constructive engagement nor that hope establishes endorsement of an unspecified future text or a future vote.""",
    "8923-IND": """India supports adequate, sustainable resources, training and logistical support for the G-5 Sahel Joint Force: the existing support model is inadequate. We remain willing to expand capacity-building assistance to affected countries' armed forces against terrorism.

Climate change is a defining challenge and can exacerbate conflict. That does not justify treating climate as the sole explanation of conflict or as an excuse for terrorism. We oppose a separate Security Council climate-security track and retain the holistic, consensus-based UNFCCC process with all developing countries participating.

This institutional objection does not diminish our climate commitments. We remain committed to the Paris Agreement and Glasgow outcomes, including net zero by 2070. Developed countries must meet equitable obligations for mitigation, adaptation, climate finance and technology transfer; we urge climate financing of $1 trillion at the earliest. These are real policy commitments. The supplied statement does not establish endorsement of an unspecified future Council text or a future vote.""",
    "8923-GBR": """The United Kingdom regards climate change as a threat multiplier for fragile and conflict-affected societies. In the Sahel, rainfall changes have fuelled farmer-herder conflict and can create conditions for violent extremism; climate is not a complete explanation of terrorism.

The Glasgow Climate Pact keeps the hope of 1.5 degrees alive. Commitments on net zero, ending and reversing deforestation, doubling adaptation financing and meeting the $100 billion goal by 2023 at the latest can strengthen preparedness.

We support comprehensive UN reporting on climate-security links. The Counter-Terrorism Committee Executive Directorate should examine conditions in which terrorism develops; all UN bodies, including the Security Council, have a role. Our support for the submitted draft resolution is explicit, rather than unknown. Women and girls must participate meaningfully in a fully inclusive approach. These positions do not establish a later recorded vote or endorsement of an unspecified future text.""",
}


def digest(value):
    return hashlib.sha256(value).hexdigest()


def build():
    original = [json.loads(line) for line in (PRIOR/"pack/train.jsonl").read_text().splitlines()]
    wps = json.loads(WPS.read_text())
    bodies = {r["id"]:r["body"] for r in original}
    bodies.update({"8514-"+c:r["text"] for c,r in wps.items()})
    proof = []
    points = {}
    for ident, entries in POINTS.items():
        body = bodies[ident]
        points[ident] = []
        for key, claim, anchors in entries:
            support = []
            for anchor in anchors:
                start=body.index(anchor)
                support.append(dict(start=start,end=start+len(anchor),quote=anchor))
            points[ident].append(dict(id=key,claim=claim,support=support))
        points[ident].append(dict(id="future_authority",claim="No endorsement of an unspecified future text or future vote is established. Preserve real ongoing commitments and known historical actions.",support=[],kind="bounded_scope_not_absence_of_real_policy"))
        proof.append(dict(id=ident,body_sha256=digest(body.encode()),source_kind="complete_country_statement",points=points[ident]))
    sanctions=(PRIOR/"sources/record-9214.txt").read_text()
    a=sanctions.index("In favour:");b=sanctions.index("I shall now give the floor",a)
    vote=sanctions[a:b].strip()
    assert "Abstaining: India" in vote and "United Kingdom" in vote and "resolution 2664 (2022)" in vote
    for ident in ["9214-IND","9214-GBR"]:
        claim = ("India abstained on adopted resolution2664; this is an observed past vote, not a prediction." if ident.endswith("IND")
                 else "UK voted in favour of adopted resolution2664; this is an observed past vote, not a prediction.")
        points[ident].insert(0,dict(id="recorded_vote",claim=claim,support=[],kind="protocol_record",quote=vote))
    episodes = {"9214":dict(date="2022-12-09",topic="General issues relating to sanctions; national post-vote statements after adoption of resolution2664",countries=["IND","GBR"]),
                "8923":dict(date="2021-12-09",topic="Climate, security and terrorism in the Sahel; national statements, not a supplied subsequent vote",countries=["IND","GBR"]),
                "8514":dict(date="2019-04-23",topic="Women, peace and security; national post-vote statements after adoption of resolution2467",countries=["FRA","GBR"])}
    rows=[]
    for episode,scene in episodes.items():
        common="SCENARIO\nUN Security Council; "+scene["date"]+"; "+scene["topic"]+".\nPublic institutional positions, not population beliefs or private motives. No new government instruction is supplied.\n\nCOMPLETE COUNTRY SOURCES\n"
        for c in scene["countries"]:
            common += "\n["+episode+"-"+c+"]\n"+bodies[episode+"-"+c]+"\n"
        if episode=="9214":common += "\nRECORDED PROCEDURE\n"+vote+"\n"
        common += "\nCHECKED FACT MAP (same-assistant source paraphrases; independent review pending)\n"
        for c in scene["countries"]:
            common += "\n"+c+" | national delegation | "+scene["date"]+"\n"
            common += "\n".join("- "+p["id"]+": "+p["claim"] for p in points[episode+"-"+c])+"\n"
        for c in scene["countries"]:
            ident=episode+"-"+c
            rows.append(dict(id=ident,country=c,episode=episode,split="eval" if episode=="8514" else "train",
                messages=[dict(role="system",content=SYSTEM),dict(role="user",content=common+"\nREQUESTED ROLE: "+c+" national delegation.")],
                target=TARGETS.get(ident),units={p["id"]:p["claim"] for p in points[ident]}))
    assert len(rows)==6 and len(TARGETS)==4
    for row in rows:
        assert row["target"] is None or len(row["target"].split())<=240
        assert row["target"] is None or row["target"] not in row["messages"][1]["content"]
    old_wps=json.loads((ROOT/"data/prepared/synthesis-rehearsal-wps-20261006-v1/criteria.json").read_text())["wps"]
    applications=[]
    for row in rows:
        if row["episode"]!="8514":continue
        country=row["country"]
        content,role=row["messages"][1]["content"].split("\nREQUESTED ROLE:")
        content += (
            "\nHYPOTHETICAL APPLICATION P (not an actual government proposal or endorsement): P calls itself survivor-centred but withholds all care until a final conviction and omits comprehensive sexual/reproductive services. "
            "In addition to preserving the supplied national facts, apply the following provided analytical plan, clearly identifying it as a recommendation for this exercise: "
            "revise P to provide immediate comprehensive sexual/reproductive care without a conviction gate; fund a survivor-referral route for care and a separate voluntary protected referral route for investigation/prosecution. "
            "Parallel care and justice require staffing/funding/coordination, but waiting for conviction harms access. "
            "Do not present these operational recommendations or opposition to P as an actual statement by the historical delegation. The record establishes real continuing care commitments, but not official endorsement of P or a future vote."
        )
        applications.append({**row,"id":"application-"+row["id"],"split":"application_eval",
            "messages":[row["messages"][0],dict(role="user",content=content+"\nREQUESTED ROLE:"+role)],
            "units":dict(old_wps["common"]+old_wps["specific"][country]),"rubric_origin":"original WPS 12-unit national inventory; new role-specific supplied-plan inputs, original grades unchanged"})
    rows += applications
    return rows,dict(statements=bodies,grounding=proof,recorded_vote=dict(path=str((PRIOR/"sources/record-9214.txt").relative_to(ROOT)),start=a,end=a+len(vote),quote=vote),
                     source_rows_path=str((PRIOR/"pack/train.jsonl").relative_to(ROOT)),wps_path=str(WPS.relative_to(ROOT)))


if __name__=="__main__":
    if (OUT/"release.json").exists():
        raise ValueError("Frozen release exists; use another version")
    OUT.mkdir(exist_ok=True)
    rows,proof=build()
    (OUT/"examples.json").write_text(json.dumps(rows,indent=2,ensure_ascii=False)+"\n")
    (OUT/"grounding.json").write_text(json.dumps(proof,indent=2,ensure_ascii=False)+"\n")
    for row in rows:
        (OUT/(row["id"]+".txt")).write_text("\n\n".join(m["role"].upper()+"\n"+m["content"] for m in row["messages"])+("\n\nTRAINING TARGET\n"+row["target"] if row["target"] else "\n\nNO FITTING TARGET")+"\n")
    print(json.dumps([dict(id=r["id"],split=r["split"],units=len(r["units"]),target_words=None if r["target"] is None else len(r["target"].split())) for r in rows]))
