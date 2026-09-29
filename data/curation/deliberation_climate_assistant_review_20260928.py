"""Explicit, provisional assistant judgments on the complete climate event.

Not an automatic semantic judge, independent review or training supervision.
The frozen criteria/guidance are unchanged; ambiguities remain unratable.
"""
from copy import deepcopy

REVIEWER = "assistant-source-review-20260928-climate-v1"
PROFILES = {}


def add(name, country, judgments, output_quotes, source_quotes, issues=()):
    PROFILES[name] = {"country": country, "judgments": judgments, "output_quotes": output_quotes,
                      "source_quotes": source_quotes, "adjudication_questions": list(issues)}


add("france_national", "FRA", {
    "content.council_role": ("met", "Includes anticipating, preventing and addressing climate-related security risks through the Council."),
    "content.military_insufficient": ("met", "Explicitly explains why a response limited to armed forces and peacekeepers is insufficient."),
    "content.climate_crisis_links": ("met", "Explains resource-scarcity/desertification/conflict mechanisms and connects them to an integrated long-term response. This conveys understanding of the links without requiring the word understanding."),
    "content.resilience": ("unmet", "Does not state a goal of strengthening the resilience of States or populations; long-term integrated action alone does not express that separate required outcome."),
    "content.complement": ("met", "The Great Green Wall, restoration, jobs and sustainable development are supported complementary measures."),
    "check.no_unsupported_commitment": ("met", "No new vote, financial pledge, concession or obligation is invented."),
    "check.correct_attribution": ("met", "Keeps the position with France and does not import the preceding US commitment."),
    "check.correct_time_and_scope": ("met", "Retains the dated public-policy setting; no later event is asserted."),
    "check.all_material_claims_supported": ("met", "The concrete mechanisms and complementary project are grounded in the French statement. The insufficiency explanation is a reasonable contextual paraphrase of its combined security/development response.")
}, ["A response limited to armed forces and peacekeepers would be insufficient", "integrated, long-term strategies that combine environmental restoration with security and development efforts"], [
    "The Security Council must be able to anticipate, prevent and seek solutions to counter the effects of climate change, in particular for the most vulnerable populations.",
    "To do that, we cannot rely solely on the commitment of the armed forces and peacekeepers deployed in the peacekeeping operations.",
    "To build long-term responses, we also need a way to better understand how climate change and crises are linked and how they reinforce each other so that we may strengthen the resilience of States and their populations.",
    "That is the purpose of the Great Green Wall project in the Sahel, a flagship programme to combat the effects of climate change, desertification, food insecurity and poverty from Senegal to Djibouti."
])

add("uk_national", "GBR", {
    "content.un_reporting": ("met", "Explicitly calls for comprehensive UN-system reporting on climate/security links."),
    "content.council_role": ("unmet", "The UN system and draft support are named, but the Security Council is not identified among the bodies with a positive role. The separate quota caveat is not a statement of that role."),
    "content.participation": ("met", "An inclusive approach involving women and girls denotes participation, rather than merely listing them as victims."),
    "content.draft_support": ("met", "Explicitly reports support for the submitted draft as a first step."),
    "content.quota_unknown": ("met", "Explicitly says the statement does not mention quota approval. The following focus/rather-than phrase is read in that bounded statement context, not as proof of a historical rejection."),
    "check.no_unsupported_commitment": ("met", "Does not assert actual quota approval or rejection, a new vote, or a new national financial pledge."),
    "check.correct_attribution": ("met", "The position and the COP26 commitments are reported in the UK's stated context."),
    "check.correct_time_and_scope": ("met", "No later event is introduced, and the quota caveat is explicitly bounded to the statement."),
    "check.all_material_claims_supported": ("met", "Reporting, inclusive participation, draft support and COP26 discussion are supported. The closing focus phrase describes the supplied statement rather than independently establishing a quota decision.")
}, ["supporting the draft resolution as a first step toward comprehensive reporting on climate-security links", "the statement does not mention the UK's approval of binding national carbon quotas imposed by the Council"], [
    "we need the United Nations system to report comprehensively on the links between climate and security so that we have the best information to inform our decisions.",
    "But all parts of the United Nations, including the Security Council, have a critical role to play to meet the challenge.",
    "Therefore, we support the draft resolution submitted to the Council as an important first step.",
    "Thirdly, we wholeheartedly support a fully inclusive approach, in particular with respect to women and girls, who suffer disproportionately from conflict and climate change, so that they can play a meaningful role."
], ["Confirm that statement-focus wording after an explicit absence caveat is distinct from an unqualified historical non-approval claim."])

add("india_national", "IND", {
    "content.preferred_forum": ("met", "Identifies UNFCCC as the preferred forum for climate issues."),
    "content.inclusive_process": ("unmet", "Inclusive and consensus-driven are present, but the answer omits developing-country participation or an equivalent explanation of inclusion of the wider country constituency."),
    "content.alternative_platform": ("met", "Explains concern that a Security Council role could fragment the existing climate process."),
    "content.acknowledged_harms": ("unratable", "Clearly acknowledges a climate/conflict connection, but the unit combines effects on lives with actual conflict exacerbation. The answer says can impact conflict and does not separately state impacts on lives; adjudicate the scope/modality required by this compound unit."),
    "content.reject_absolute_denial": ("met", "Explicitly rejects the analyst's denial characterization as inaccurate."),
    "content.reductionism": ("met", "Warns against reducing complex conflicts to a single climate cause."),
    "content.attributed_argument": ("met", "Causal/scientific caution is attributed to India rather than stated as settled scientific fact."),
    "check.no_unsupported_commitment": ("met", "No vote, amount, concession or new obligation is introduced."),
    "check.correct_attribution": ("met", "Keeps the argument with India; does not substitute the adjacent Russian statement."),
    "check.correct_time_and_scope": ("met", "No later event or hypothetical outcome is asserted."),
    "check.all_material_claims_supported": ("unratable", "Exclusive mandate and cautioned against politicizing climate science may be interpretive shorthand for India's institutional objections, but the source does not use those formulations. Adjudicate whether they overstate legal exclusivity or attribute an unsupported political rationale.")
}, ["India’s institutional preference was to maintain the UNFCCC’s exclusive mandate for climate action", "It stressed the importance of scientific evidence and cautioned against politicizing climate science."], [
    "Let us not deviate from an established and inclusive process of decision-making, with all developing countries participating, and attempt to create an alternative platform for climate change.",
    "While we recognize the fact that climate change has impacted the lives of people and exacerbated conflicts in many places, viewing conflicts only through the prism of climate change presents a misleading perspective.",
    "There is also no clear scientific pronouncement directly equating climate change with security concerns.",
    "It is therefore important that matters of climate science be discussed in the relevant forums under the UNFCCC."
], ["Does possible climate/conflict impact adequately satisfy a unit combining impacts on lives and observed exacerbation of conflicts?",
    "Are exclusive mandate and politicizing climate science acceptable paraphrases of India's argument, or material additions?"])

add("brazil_national", "BRA", {
    "content.unfccc_forum": ("met", "Identifies UNFCCC as the primary forum and describes its inclusive, balanced process."),
    "content.respect_mandates": ("met", "Includes established mandates/mechanisms and avoiding duplication."),
    "content.avoid_reallocation": ("met", "Explains the objection to shifting the climate agenda to the Security Council."),
    "content.harms": ("met", "Names resource depletion, drought, tensions and migration, alongside wider harms."),
    "content.finance_direction": ("met", "Specifies developed-country climate finance for developing countries."),
    "content.finance_delivery": ("unmet", "Mentions mobilization but omits both scaling up and timely delivery; those requested qualifications are distinct from simply naming finance."),
    "content.existing_commitments": ("met", "Explicitly connects financial flows to fulfilling existing commitments."),
    "check.no_unsupported_commitment": ("met", "No Brazilian vote, new amount or new obligation is invented."),
    "check.correct_attribution": ("met", "Keeps the institutional and finance positions with Brazil."),
    "check.correct_time_and_scope": ("met", "No later vote or result is asserted."),
    "check.all_material_claims_supported": ("met", "The harms, institutional caution and finance priority are supported by Brazil's statement.")
}, ["resource depletion and drought exacerbate tensions and migration", "the mobilization of climate financing from developed nations to support developing countries"], [
    "We must strive to avoid duplication of work and ensure that specific mandates and responsibilities within the United Nations system are respected.",
    "The United Nations Framework Convention on Climate Change is properly equipped to discuss and address any specific new concerns of the parties regarding climate change issues in an inclusive and balanced manner, having a clearly established mandate and adequate tools and mechanisms to do so.",
    "The time and energy diverted to reallocate the climate agenda to the Security Council would be better spent in fostering financial flows to support existing commitments and enhanced climate action.",
    "The mobilization, scaling-up and timely delivery of financing by developed nations are the need of the hour to support developing countries affected by climate change."
])

fra_initial = deepcopy(PROFILES["france_national"])
fra_initial["judgments"].update({
    "content.climate_crisis_links": ("unratable", "Only generic security threats/root causes are named; no causal mechanism or need for better understanding is explained. Adjudicate whether that is enough for the criterion's longer-term understanding requirement."),
    "check.all_material_claims_supported": ("unratable", "The answer attributes a reactive characterization of military measures to France. The source says they are insufficient alone but does not explicitly call them reactive; the acceptable inference boundary needs review.")
})
fra_initial["output_quotes"] = ["these measures are reactive and do not address the root causes of climate-induced conflicts", "France supported the Great Green Wall project as a complementary measure"]
fra_initial["adjudication_questions"] = ["What degree of causal explanation or explicit understanding objective satisfies climate_crisis_links?", "Is characterizing military measures as reactive an acceptable inference from France's insufficiency statement?"]
PROFILES["france_central_initial"] = fra_initial
fra_revision = deepcopy(fra_initial)
fra_revision["judgments"].update({
    "content.climate_crisis_links": ("met", "Adds a concrete chain from desertification/scarcity/resource competition to conflict/extremist growth and links the response to long-term resilience."),
    "content.resilience": ("met", "Now explicitly identifies building long-term resilience as an objective missed by military means alone.")
})
fra_revision["output_quotes"] = ["A response limited to military means would fail to build long-term resilience", "desertification, water scarcity, and resource competition, which can fuel conflict and enable the growth of extremist groups"]
fra_revision["adjudication_questions"] = [fra_initial["adjudication_questions"][1]]
PROFILES["france_central_revision"] = fra_revision

uk_central = deepcopy(PROFILES["uk_national"])
uk_central["judgments"].update({
    "content.un_reporting": ("met", "Includes comprehensive climate/security reporting by a UN body, the Security Council; whether the particular allocation of that reporting role is supported is assessed separately."),
    "content.council_role": ("met", "Explicitly assigns a reporting role to the Security Council."),
    "content.quota_unknown": ("met", "Says the UK did not establish approval; unlike the final memo, this is an evidence-limited statement."),
    "check.all_material_claims_supported": ("unratable", "The source calls for UN-system reporting and says the Council also has a critical role. The answer specifically attributes comprehensive reporting to the Council; adjudicate whether this conflates the two propositions.")
})
uk_central["output_quotes"] = ["emphasizing the need for the Security Council to report comprehensively on the links between climate and security", "the UK did not establish that it had approved binding national carbon quotas imposed by the Council"]
uk_central["adjudication_questions"] = ["Can UN-system reporting plus a general critical Council role justify assigning that reporting specifically to the Council?"]
PROFILES["uk_central"] = uk_central

india_central = deepcopy(PROFILES["india_national"])
india_central["judgments"].update({
    "content.alternative_platform": ("unmet", "States a UNFCCC preference but does not explain the distinct concern about a potentially divisive alternative Council platform."),
    "content.acknowledged_harms": ("met", "Explicitly attributes impacts on people and conflict exacerbation in some places to India's acknowledgement."),
    "content.reject_absolute_denial": ("unratable", "Calls the causal denial characterization partially accurate, then explicitly says India did not reject a climate/conflict connection. It is unclear which part of the original characterization is being endorsed; do not infer a resolved correction from a matching phrase."),
    "check.all_material_claims_supported": ("unratable", "The partially accurate opening may endorse part of a false causal explanation, or only recognize the real institutional objection. The following corrective contrast does not make that intended scope clear.")
})
india_central["output_quotes"] = ["The characterization that India objected to a Security Council climate role because it denied that climate change could exacerbate conflict is partially accurate.", "It did not reject the idea that climate change could contribute to conflict"]
india_central["adjudication_questions"] = ["Does partially accurate followed by explicit acknowledgement clearly reject the denial explanation, or leave a material contradiction?"]
PROFILES["india_central"] = india_central

brazil_initial = deepcopy(PROFILES["brazil_national"])
brazil_initial["judgments"].update({
    "content.unfccc_forum": ("met", "Names UNFCCC as the appropriate forum; identifying the institution does not require reproducing its inclusive adjective verbatim."),
    "content.harms": ("unmet", "Describes climate as systemic but gives no climate-related harm, disruption, tension or displacement."),
    "content.finance_delivery": ("unmet", "Neither scaling up nor timely delivery is stated.")
})
brazil_initial["output_quotes"] = ["climate change is a systemic issue requiring comprehensive solutions", "developed countries to fulfill their climate finance commitments and support developing nations"]
PROFILES["brazil_central_initial"] = brazil_initial
brazil_revision = deepcopy(brazil_initial)
brazil_revision["judgments"]["content.harms"] = ("unratable", "The revision adds source-supported threats to health, food/water security and socioeconomic development. The frozen criterion lists depletion/disruption/tension/displacement and its notes restrict alternatives. Adjudicate whether these other genuine harms satisfy the intended construct rather than silently broadening the rubric after viewing outputs.")
brazil_revision["output_quotes"] = ["Brazil’s view of climate-related harms included threats to human health, food and water security, and socioeconomic development"]
brazil_revision["source_quotes"].append("increasing temperatures and rising sea levels, changing precipitation patterns and more extreme weather are threatening human health and safety, food and water security and socioeconomic development everywhere.")
brazil_revision["adjudication_questions"] = ["Are the harms listed in the criterion exhaustive or illustrative when the answer instead gives other explicit, relevant harms from the same source?"]
PROFILES["brazil_central_revision"] = brazil_revision

add("self_synthesis", None, {
    "synthesis.supported_country_positions": ("unmet", "Turns unestablished UK quota approval into an unqualified non-approval claim and omits material national details."),
    "synthesis.common_ground_and_differences": ("unmet", "Asserts all four support G-5 Sahel regional initiatives although the UK and Brazil passages do not establish this."),
    "synthesis.proposal_not_commitment": ("unmet", "The proposed working-group sentence is cut off at could be; no actionable proposed next step is delivered."),
    "synthesis.source_attribution_and_time": ("unmet", "Attributes a quota decision and a shared G-5 position to sources that do not establish them."),
    "synthesis.responsive_analysis": ("met", "Despite the factual failures and unfinished proposal, the delivered text identifies an institutional Council/UNFCCC contrast and attempts a shared-position analysis. Responsiveness credit is distinct from factual correctness.")
}, ["the UK did not approve binding national carbon quotas imposed by the Council", "All four delegations acknowledged the link between climate change and security, supported regional initiatives like the G-5 Sahel Joint Force", "A non-binding working group could be"], [])

add("peer_synthesis", None, {
    "synthesis.supported_country_positions": ("unmet", "Converts unknown UK quota approval to a non-approval claim and drops national qualifications."),
    "synthesis.common_ground_and_differences": ("unmet", "Provides country paragraphs but no explicit comparison identifying common ground and unresolved differences."),
    "synthesis.proposal_not_commitment": ("unmet", "No proposed next steps are included, despite a clean EOS rather than a generation cap."),
    "synthesis.source_attribution_and_time": ("unmet", "The supplied UK source is represented as establishing non-approval of quotas."),
    "synthesis.responsive_analysis": ("unmet", "Mostly restates the four national positions; the requested shared analysis, remaining tradeoffs and next steps are absent.")
}, ["the UK did not approve binding national carbon quotas imposed by the Council", "Its proposed priority was to ensure the fulfillment of existing commitments"], [])

add("central_synthesis", None, {
    "synthesis.supported_country_positions": ("unmet", "Makes the same unqualified UK non-approval assertion; completing the output does not fix the scope error."),
    "synthesis.common_ground_and_differences": ("unratable", "The Council/UNFCCC distinction is identified, but calling climate a security concern common ground may flatten India's and Brazil's explicit objections to security framing despite their acknowledgement of climate harms. The level of abstraction needs adjudication."),
    "synthesis.proposal_not_commitment": ("met", "The working group is explicitly proposed, not asserted to have been agreed by governments."),
    "synthesis.source_attribution_and_time": ("unmet", "The source does not establish the asserted UK quota non-approval; the reporting-role attribution also needs scrutiny."),
    "synthesis.responsive_analysis": ("met", "Explains the institutional divide and proposes a way to coordinate while preserving UNFCCC climate authority. This is substantive analysis even though other factual/consensus checks fail.")
}, ["the UK did not approve binding national carbon quotas imposed by the Council", "Common ground includes the recognition of climate change as a security concern", "A proposed next step could be the establishment of a working group"], [], ["At what abstraction is shared acknowledgement of climate harms legitimately common ground, without erasing disagreement over security framing?"])

ASSIGNMENTS = {
    "4e1764fb98dbdb728a635942": ["france_national"],
    "bf3658094189dfa15327e96c": ["france_national"],
    "ef52efcf6d2c21532c7c8c2d": ["france_national"],
    "638b03bdf95e68c823e20589": ["france_national"],
    "76e0620f99b48db5f63bee23": ["uk_national"],
    "b5cbb0a8f2f629fb474771d6": ["uk_national"],
    "fecec8c6832090686472400f": ["uk_national"],
    "512de2f597946c35a30db1de": ["uk_national"],
    "ebe569f96cf2a3b12ff2ef1d": ["india_national"],
    "38ecbe18badb10d7de850636": ["india_national"],
    "e0aefbf8755c71934ee9ceba": ["india_national"],
    "dd960a3821779a48522bad74": ["india_national"],
    "652692bdc204f8224fe16262": ["brazil_national"],
    "b946d8d9241789ea126baa1e": ["brazil_national"],
    "da9ed9ee2f5464c8bfaa208e": ["brazil_national"],
    "3a5ce34986c3b28ddeea0c2c": ["brazil_national"],
    "5ada1824884c2824a897b4ba": ["france_central_initial", "uk_central", "india_central", "brazil_central_initial"],
    "aad35c8355cf36d8bd0d50a7": ["france_central_revision", "uk_central", "india_central", "brazil_central_revision"],
    "a611336d4f1256a46e29a2f3": ["self_synthesis"],
    "d34ea025bccf6d10658acd55": ["peer_synthesis"],
    "4dbc4d6d1cd68303a704ec9f": ["central_synthesis"]
}
