"""Exact-span records of the assistant review of the six opaque candidates."""
import json

from score import CASE, HERE

EVIDENCE = {row["id"]: row["text"] for row in CASE["evidence"]}
VOTE = "On 9 December 2022, the Council adopted Resolution 2664 by 14 votes in favour, with India abstaining."
VOTE_REASON = "The answer gives the date, instrument, affirmative tally and abstention. It omits the count against."
TERM_REASON = "The candidate omits the Council's stated intent to decide on extension before expiry."
SCOPE_REASON = "Exemption of the necessary transactions from asset freezes is distinct from exemption of actors from supplying those resources."
DILIGENCE_REASON = "The text requests reasonable efforts to minimize prohibited benefits, including through due diligence. It does not impose a stronger duty to achieve minimization."
ROWS = {
    "55c49c0e8248b8cb5311": {
        "scope": ("unmet", "exempting qualifying actors from providing resources", SCOPE_REASON),
        "term": ("unmet", "two-year exemption for ISIL and Al-Qaida", TERM_REASON),
        "safeguards": ("unmet", "assigns monitoring to the 1267 Committee and sanctions bodies, urging providers to minimize prohibited benefits", "Identifies the monitoring role and objective but omits due diligence."),
        "india": ("met", "India objected, warning of diversion risks by ISIL and Al-Qaida and demanding proactive 1267 Monitoring Team involvement and robust reporting standards. India judged these specific safeguards insufficiently addressed in the adopted text.", "The national speaker and direction of its position are explicit."),
        "relation": ("met", "While the Council granted the exemption and assigned monitoring, India's concerns regarding diversion risks and reporting gaps remain unresolved.", "The sentence directly contrasts the Council's safeguards with the national assessment described immediately before it."),
        "guard": ("failed", "exempting qualifying actors from providing resources", ("scope",), SCOPE_REASON),
    },
    "5dc94b6e1239c97d64d7": {
        "scope": ("met", "preserves asset-freeze obligations while exempting qualifying actors providing resources for timely humanitarian assistance or basic human needs", "Limits the exemption to qualifying actors when providing the specified assistance or basic-needs resources and preserves the underlying freezes."),
        "term": ("unmet", "A two-year exemption applies to ISIL and Al-Qaida regimes, subject to review.", TERM_REASON),
        "safeguards": ("unmet", "Providers must minimize prohibited benefits through due diligence.", DILIGENCE_REASON),
        "india": ("met", "India objected, warning of diversion risks and seeking proactive involvement by the 1267 Monitoring Team and robust reporting mechanisms. India judged these concerns not fully addressed in the adopted text", "Includes the reason, desired oversight and assessment in India's voice."),
        "relation": ("met", "The Council's actions established the exemption and monitoring framework; India's assessment remained that the adopted text lacked sufficient proactive oversight mechanisms to fully address diversion risks.", "Expressly links adopted oversight to the national view that it remained insufficient."),
        "guard": ("failed", "Providers must minimize prohibited benefits through due diligence.", ("safeguards",), DILIGENCE_REASON),
    },
    "6506f7a4f3a235aad6e4": {
        "scope": ("unmet", "exempting qualifying actors from providing resources", SCOPE_REASON),
        "term": ("unmet", "This exemption applies to ISIL and Al-Qaida for two years", TERM_REASON),
        "safeguards": ("unmet", "mandating due diligence to minimize prohibited benefits", "Treats a request for reasonable efforts as a mandate."),
        "india": ("met", "India objected, warning of diversion risks and judging the text failed to address its concerns regarding proactive involvement by the Monitoring Team and robust reporting mechanisms.", "States India's warning and wanted changes. The later phrase 'did not sufficiently' qualifies the assessment."),
        "relation": ("met", "The Council's safeguards, specifically the due diligence requirement and the 1267 Committee's monitoring mandate, were intended to mitigate these risks. However, India maintained that the adopted measures did not sufficiently ensure oversight or prevent diversion.", "The stated relation between committee monitoring and India's insufficiency assessment is supported. The separate claim about a due diligence requirement is downgraded under safeguards."),
        "guard": ("failed", "exempting qualifying actors from providing resources", ("scope",), SCOPE_REASON),
    },
    "6da88eebf28dd9435702": {
        "scope": ("unmet", "exempting qualifying actors from providing or processing resources", SCOPE_REASON),
        "term": ("unmet", "two-year exemption for ISIL and Al-Qaida regimes", TERM_REASON),
        "safeguards": ("unmet", "includes due diligence requirements to minimize prohibited benefits", "Presents the request for reasonable efforts through due diligence as a requirement."),
        "india": ("met", "India objected, warning of diversion risks and urging proactive 1267 Monitoring Team involvement and robust reporting standards. It judged these specific concerns not fully addressed in the adopted text.", "States the warning, the two requested measures and the assessment."),
        "relation": ("met", "The Council's safeguards aim to balance oversight with operational flexibility, though India felt the resolution failed to resolve its identified gaps regarding monitoring and reporting mechanisms.", "Connects the adopted safeguards, including identified committee monitoring, to India's assessment of the specific gaps."),
        "guard": ("failed", "exempting qualifying actors from providing or processing resources", ("scope",), SCOPE_REASON),
    },
    "6ff2dac496f3b335d868": {
        "scope": ("met", "preserves asset-freeze obligations while exempting qualifying actors providing resources for timely humanitarian assistance or basic human needs", "Limits the exemption to qualifying actors supplying the specified resources and preserves the underlying freezes."),
        "term": ("unmet", "two-year exemption for ISIL and Al-Qaida regimes", TERM_REASON),
        "safeguards": ("unmet", "includes due diligence requirements to minimize prohibited benefits", "Identifies committee monitoring afterward, but presents a request for reasonable efforts as a requirement."),
        "india": ("met", "India had warned of diversion risks and sought proactive Monitoring Team involvement and robust reporting standards, judging these concerns not fully addressed.", "States India's warning, stronger oversight request and assessment. The team is identifiable in the accompanying 1267 context."),
        "relation": ("met", "The Council's framework, however, establishes oversight mechanisms to ensure compliance while allowing time for targeted measures, distinguishing the adopted safeguards from India's specific objections regarding monitoring depth.", "Connects the explicitly identified committee oversight to India's specific objections. The statement about allowing time for targeted measures is extra."),
        "guard": ("failed", "includes due diligence requirements to minimize prohibited benefits", ("safeguards",), "Recasts the requested reasonable efforts as a mandatory due diligence requirement."),
    },
    "d4d48fc9fb8bfbc071c9": {
        "scope": ("unmet", "exempting qualifying actors from providing or processing resources", SCOPE_REASON),
        "term": ("unmet", "the text granted a two-year exemption and assigned monitoring roles", "The sentence does not limit this period to the specified regime or preserve the intended decision on extension."),
        "safeguards": ("unmet", "assigned monitoring roles to the 1267 Committee and sanctions bodies", "Includes a monitoring role but omits requested provider due diligence."),
        "india": ("met", "India judged these measures insufficient to address diversion risks under the ISIL/Al-Qaida regime. The Indian representative urged proactive Monitoring Team involvement and robust reporting mechanisms, noting these specific concerns were not fully addressed in the final text.", "Includes the expressed reason, oversight request and national assessment. The specific regime identifies the Team."),
        "relation": ("met", "Regarding safeguards, the text granted a two-year exemption and assigned monitoring roles to the 1267 Committee and sanctions bodies. India judged these measures insufficient to address diversion risks under the ISIL/Al-Qaida regime.", "The reference to 'these measures' explicitly relates India's assessment to the immediately preceding adopted monitoring."),
        "guard": ("failed", "exempting qualifying actors from providing or processing resources", ("scope",), SCOPE_REASON),
    },
}


def citations(keys):
    return [{"block": key, "quote": EVIDENCE[key]} for key in keys]


def marks():
    sources = {"vote": ("vote",), "scope": ("scope",), "term": ("safeguards",),
               "safeguards": ("safeguards",), "india": ("india",), "relation": ("safeguards", "india")}
    annotated = {}
    for key, row in ROWS.items():
        units = []
        for criterion, source_ids in sources.items():
            status, span, reason = ("unmet", VOTE, VOTE_REASON) if criterion == "vote" else row[criterion]
            units.append({"id": criterion, "status": status, "response": span,
                          "source": citations(source_ids), "reason": reason})
        status, span, source_ids, reason = row["guard"]
        annotated[key] = {"id": key, "units": units,
                          "guard": {"status": status, "response": span,
                                    "source": citations(source_ids), "reason": reason}}
    return annotated


if __name__ == "__main__":
    print(json.dumps(marks(), ensure_ascii=False, indent=2))
