"""Explicit assistant annotations, not an automatic judge or training targets.

These provisional judgments were made after reading the full four-country source
packet and all 21 Ukraine outputs. Profiles reuse identical judgments across
specified responses; materialization verifies every output/source excerpt.
"""
from copy import deepcopy

REVIEWER = "assistant-source-review-20260928-ukraine-v1"
PROFILES = {}


def add(name, country, judgments, output_quotes, source_quotes, issues=()):
    PROFILES[name] = {"country": country, "judgments": judgments, "output_quotes": output_quotes,
                      "source_quotes": source_quotes, "adjudication_questions": list(issues)}


add("france_national", "FRA", {
    "content.capacity": ("met", "Explicitly rejects Council unanimity and identifies France's own position."),
    "content.nonrecognition": ("met", "Reports rejection of the illegal annexation attempts in the current Ukraine context."),
    "content.continued_support": ("met", "Explicitly states continued support for Ukraine."),
    "content.support_duration": ("met", "Preserves the as-long-as-necessary duration."),
    "content.support_purpose": ("met", "The paragraph links France's continuing stance/support to Ukraine's sovereignty and territorial integrity; this is an acceptable umbrella paraphrase."),
    "content.pledge_unknown": ("met", "Explicitly says there is no exact financial pledge in the statement."),
    "check.no_unsupported_commitment": ("unmet", "Calling the support unconditional broadens the documented duration/purpose statement into an unsupported commitment."),
    "check.correct_attribution": ("met", "National versus Council capacity is correctly distinguished."),
    "check.correct_time_and_scope": ("met", "No later vote or observed hypothetical event is introduced. The commitment overstatement is recorded separately."),
    "check.all_material_claims_supported": ("unmet", "The source commits support for as long as necessary for stated purposes; it does not explicitly establish unconditional support.")
}, ["The support for Ukraine is framed as ongoing and unconditional", "does not specify an exact financial pledge"], [
    "I shall now make a statement in my capacity as the representative of France.",
    "France will never recognize those illegal annexation attempts by Russia.",
    "France will continue to provide Ukraine with the support it needs for as long as is necessary in order to ensure respect for its independence, sovereignty and territorial integrity."
], ["Confirm the materiality of unconditional as an added commitment; do not treat a duration qualifier as equivalent to absence of conditions."])

add("uk_national", "GBR", {
    "content.illegitimate_referendums": ("met", "Rejects the referendums as sham, coercive and illegitimate."),
    "content.sovereignty": ("met", "Connects the rejection to Ukrainian sovereignty and territorial integrity."),
    "content.draft_support": ("met", "Reports UK support for the US/Albania draft."),
    "content.time_scope": ("unmet", "Claims a later recorded vote is established by S/PV.9135, although the source references remarks last week."),
    "check.no_unsupported_commitment": ("unmet", "Invents a recorded vote and a claim that no later vote contradicted the position."),
    "check.correct_attribution": ("met", "The country and speaker are UK/Kariuki; the event/date error is a separate failure."),
    "check.correct_time_and_scope": ("unmet", "An earlier public statement is recast as a later recorded vote."),
    "check.all_material_claims_supported": ("unmet", "Neither the alleged vote nor the asserted absence of a contradicting later vote is established by the packet.")
}, ["A later recorded vote, referenced in S/PV.9135, confirmed the UK's support for the draft resolution",
    "No distinct later recorded vote contradicted the UK's stated position"], [
    "As my Foreign Secretary told the Council last week (see S/PV.9135), we know that President Putin is planning to rig the outcome.",
    "support the draft resolution the United States and Albania have brought forward today."
])

add("india_grouped_aid", "IND", {
    "content.cease_hostilities": ("met", "Calls for an immediate cessation of hostilities."),
    "content.negotiations": ("met", "Calls for dialogue/diplomacy and negotiations."),
    "content.legal_order": ("met", "Names international law and the UN Charter."),
    "content.sovereign_integrity": ("met", "Names sovereignty and territorial integrity."),
    "content.ukraine_assistance": ("met", "Humanitarian assistance to Ukraine is included, although the grouping of assistance types/recipients is ambiguous."),
    "content.global_south_support": ("unratable", "Economic assistance to Global South nations is present, but the source's neighbours/some scope is omitted. The rubric warns against narrowing, without settling this broader paraphrase; adjudicate materiality."),
    "content.cost_channels": ("unmet", "Food, fuel and fertilizer cost channels are all omitted."),
    "content.vote_unknown": ("met", "Explicitly declines to infer a definite Y/N/A vote from the speech."),
    "check.no_unsupported_commitment": ("unratable", "Humanitarian and economic assistance to Ukraine and other Global South nations could distribute both assistance types across all recipients or summarize them collectively. Do not force that ambiguous grammar into a definitive invented-commitment label."),
    "check.correct_attribution": ("met", "India's speaker, minister and Prime Minister are correctly associated with its position."),
    "check.correct_time_and_scope": ("unmet", "The draft's alleged submission three days later is not established by India's speech; a later vote date does not establish a submission date."),
    "check.all_material_claims_supported": ("unmet", "The claimed later submission date exceeds the source evidence, independently of the ambiguous assistance wording.")
}, ["humanitarian and economic assistance to Ukraine and other Global South nations", "which was submitted three days later"], [
    "India has repeatedly called for an immediate cessation of hostilities and has underscored the need to resolve the ongoing conflict through dialogue and diplomacy.",
    "We firmly believe that the global order should be anchored in international law, the Charter of the United Nations and respect for the sovereignty and territorial integrity of States.",
    "we provide both humanitarian assistance to Ukraine and economic support to some of our neighbours in the global South that are under economic distress, even as they stare at the escalating costs of food, fuel and fertilizer"
], ["Does Global South nations without neighbours preserve enough of the beneficiary scope for this criterion?",
    "How should coordinated aid-type/recipient phrases be judged when the grammar permits both collective and distributive readings?"])

add("brazil_initial_or_self", "BRA", {
    "content.possible_legitimacy": ("met", "Explicit self-determination plus conditional validity leaves open legitimate use of a referendum."),
    "content.conditional_validity": ("met", "Explains that procedural/legal conditions matter; a referendum is not automatically valid."),
    "content.free_will_under_conflict": ("unmet", "Criticizes current fairness and mentions conflict generally, but does not explain the separate concern that people in conflict areas cannot be assumed able to express free will."),
    "content.procedural_condition": ("met", "Includes transparency, freedom of expression and independent monitoring."),
    "content.current_referendums": ("met", "Clearly reports Brazil's negative assessment of the current referendums."),
    "content.integrity_or_negotiation": ("met", "Includes an immediate ceasefire and peace negotiations."),
    "content.recognition_unknown": ("met", "Explicitly leaves hypothetical recognition undetermined; conditions are presented as necessary, not a sufficient recognition promise."),
    "check.no_unsupported_commitment": ("met", "No automatic recognition or historical vote for the hypothetical is asserted."),
    "check.correct_attribution": ("unmet", "Attributes a Russian motive to legitimize illegal occupation to Brazil's assessment; that rationale is not in Brazil's statement."),
    "check.correct_time_and_scope": ("met", "Keeps the future referendum hypothetical."),
    "check.all_material_claims_supported": ("unmet", "The motive attributed to Brazil goes beyond its statement's escalation, free-expression and negotiation concerns.")
}, ["While Brazil acknowledged the principle of self-determination",
    "Brazil’s assessment of the then-current referendums was that they were part of a broader effort by Russia to legitimize its illegal occupation",
    "recognition remains undetermined"], [
    "recognize the inalienable right of all peoples to self-determination and to freely decide their political status.",
    "Its validity, however, depends on certain conditions.",
    "It is unreasonable to assume that populations in areas in conflict are able to freely express their will.",
    "Far from expressing the will of the people of the Donetsk, Luhansk, Kherson and Zaporizhzhya regions, the referendums tend to make the prospect of peace negotiations even more distant.",
    "We reiterate our call for an immediate ceasefire and the opening of peace negotiations."
], ["Confirm that generic references to the conflict are insufficient for the separately required freedom-under-conflict condition."])

india_peer = deepcopy(PROFILES["india_grouped_aid"])
india_peer["judgments"]["check.no_unsupported_commitment"] = ("met", "The revision explicitly separates humanitarian assistance to Ukraine from economic support to Global South nations. It does not promise a vote or new quantified assistance.")
india_peer["judgments"]["content.ukraine_assistance"] = ("met", "Specifically assigns humanitarian assistance to Ukraine.")
india_peer["output_quotes"] = ["humanitarian assistance to Ukraine and economic support to Global South nations", "which was submitted three days later"]
india_peer["adjudication_questions"] = [india_peer["adjudication_questions"][0]]
PROFILES["india_peer_revision"] = india_peer

brazil_peer = deepcopy(PROFILES["brazil_initial_or_self"])
brazil_peer["judgments"].update({
    "content.possible_legitimacy": ("unmet", "The revised answer omits self-determination, which is an explicit part of this required unit. Conditional procedural validity alone does not satisfy both parts."),
    "check.correct_attribution": ("met", "The previous explicit Brazil-attributed motive of legitimizing occupation is removed. No new country/capacity misattribution is identified."),
    "check.all_material_claims_supported": ("unratable", "As outlined in international law and the UN Charter follows a list of procedural conditions. Brazil distinguishes Charter-based self-determination from procedures recommended by international practice; the answer's broad legal attribution needs adjudication.")
})
brazil_peer["output_quotes"] = ["as outlined in international law and the UN Charter", "it called for dialogue and ceasefire", "recognition remains undetermined"]
brazil_peer["adjudication_questions"].append("Does as outlined in international law and the UN Charter materially misstate the legal source of the procedural requirements?")
PROFILES["brazil_peer_revision"] = brazil_peer

france_central = deepcopy(PROFILES["france_national"])
france_central["judgments"].update({
    "content.support_purpose": ("unratable", "Non-recognition of annexation and continuing support appear together, but the answer does not explicitly connect aid to independence/sovereignty/integrity. Adjudicate whether this counts as an equivalent umbrella formulation."),
    "check.no_unsupported_commitment": ("met", "Retains support duration and unspecified amount, without the unconditional claim present in the national-agent answers."),
    "check.all_material_claims_supported": ("met", "The France section's national attribution, non-recognition, continuing support, duration and unknown amount are source-supported.")
})
france_central["output_quotes"] = ["not as a collective Council position but as France’s own national statement", "only a commitment to provide the support Ukraine needs “for as long as is necessary.”"]
france_central["adjudication_questions"] = ["Does juxtaposing non-recognition and continuing support preserve the required support purpose without stating it explicitly?"]
PROFILES["france_central"] = france_central

uk_central = deepcopy(PROFILES["uk_national"])
uk_central["judgments"].update({
    "content.draft_support": ("unmet", "Explicitly says the UK rejected the US/Albania draft. In the revised response, later appending support while preserving rejection does not resolve the contradiction."),
    "content.time_scope": ("unmet", "Claims an eventual vote and passed resolution are established by the dated packet."),
    "check.no_unsupported_commitment": ("unmet", "Invents rejection of the draft and a later vote/outcome, while adding sanctions content not established by the packet."),
    "check.correct_time_and_scope": ("unmet", "Imports a later vote/result into analysis confined to the dated statement."),
    "check.all_material_claims_supported": ("unmet", "Draft rejection contradicts the UK source; sanctions and later passage are not established. A contradictory correction paragraph cannot cancel these claims.")
})
uk_central["output_quotes"] = ["The UK explicitly rejected the draft resolution proposed by the United States and Albania", "which sought to condemn the referendums and call for sanctions against Russia", "which passed with a majority"]
PROFILES["uk_central"] = uk_central

india_central = deepcopy(PROFILES["india_grouped_aid"])
india_central["judgments"].update({
    "content.legal_order": ("unmet", "Neither international law nor the UN Charter appears in the India section."),
    "content.ukraine_assistance": ("unmet", "Humanitarian support to affected countries does not identify Ukraine as the source-specified beneficiary."),
    "content.global_south_support": ("unmet", "The section omits Global South/neighbour beneficiaries entirely."),
    "check.no_unsupported_commitment": ("met", "General assistance wording does not make a definite new pledge, assign a definite later vote or explicitly promise aid to a new named recipient."),
    "check.correct_time_and_scope": ("met", "Leaves the later vote unknown and does not assert the unsupported submission date found in national-agent answers."),
    "check.all_material_claims_supported": ("met", "The broad claims made are compatible with the source; missing assistance detail and legal principles are scored as content omissions separately.")
})
india_central["output_quotes"] = ["humanitarian and economic support to affected countries", "it does not establish a definite Y, N, or A vote on that resolution three days later"]
india_central["adjudication_questions"] = []
PROFILES["india_central"] = india_central

brazil_central = deepcopy(PROFILES["brazil_initial_or_self"])
brazil_central["judgments"].update({
    "content.possible_legitimacy": ("unmet", "No self-determination principle is stated."),
    "content.free_will_under_conflict": ("unratable", "Links current military control to lack of genuine participation and later refers to the conflict environment. Whether that adequately expresses the independent conflict/free-will constraint is ambiguous under this unit."),
    "content.integrity_or_negotiation": ("unmet", "No territorial-integrity, ceasefire or negotiation commitment appears in the Brazil section."),
    "check.correct_attribution": ("met", "No wrong country/capacity attribution is identified; the scope of factual explanation across the shared packet is reserved below."),
    "check.all_material_claims_supported": ("unratable", "The explanation uses Russian military control from the wider common packet while presenting Brazil's negative assessment. Adjudicate whether this is acceptable source combination or an unsupported attribution of Brazil's rationale.")
})
brazil_central["output_quotes"] = ["they are held under Russian military control and lack genuine public participation", "What remains undetermined is whether the conditions for a legitimate referendum can be met in the current conflict environment."]
brazil_central["adjudication_questions"] = [
    "When does a military-control/current-participation explanation satisfy the separate conflict/free-will criterion?",
    "When does combining a fact from one country's supplied source with another country's policy become a misattributed rationale?"]
PROFILES["brazil_central"] = brazil_central

add("capped_synthesis", None, {
    "synthesis.supported_country_positions": ("unmet", "The delivered memo ends at Brazil's heading/opening and invents a later UK vote. It cannot represent all four countries faithfully."),
    "synthesis.common_ground_and_differences": ("unmet", "The delivered country paragraphs do not provide the requested comparison of common ground and remaining differences."),
    "synthesis.proposal_not_commitment": ("unmet", "No proposed next steps are delivered before truncation. Missing required proposals are not a vacuous pass for avoiding invented commitments."),
    "synthesis.source_attribution_and_time": ("unmet", "S/PV.9135 is misrepresented as a later vote, and the India section imports a submission date not established by its source."),
    "synthesis.responsive_analysis": ("unmet", "The response is incomplete before Brazil's answer and provides neither a complete comparison nor proposed next steps.")
}, ["A later recorded vote, referenced in S/PV.9135, confirmed the UK's support", "**Brazil (BRA):**  \nBrazil’s 27 September "], [])

add("central_synthesis", None, {
    "synthesis.supported_country_positions": ("unmet", "UK draft support is reversed; material national qualifications/details are also omitted."),
    "synthesis.common_ground_and_differences": ("unmet", "Country descriptions and generic next steps do not explicitly identify documented common ground and remaining material differences."),
    "synthesis.proposal_not_commitment": ("met", "The proposed-next-steps section is explicitly a proposal and assigns no new negotiated government commitment."),
    "synthesis.source_attribution_and_time": ("unmet", "A later vote and successful passage are asserted without source support; sanctions are added as draft content."),
    "synthesis.responsive_analysis": ("met", "The Brazil paragraph gives a conditional implication about future recognition and the memo offers proposed next steps. This narrow responsiveness credit does not cancel its factual failures.")
}, ["The UK rejected the draft resolution proposed by the U.S. and Albania", "which passed with a majority", "**Proposed Next Steps:**"], [])

# Explicit identities, never a classifier based on which condition should win.
ASSIGNMENTS = {
    "d089b2f78c8ed2e74f336f1c": ["france_national"],
    "2d7c5505b1d96d701bed6c86": ["france_national"],
    "f7e5d210892c238d9f618d8f": ["france_national"],
    "22dee893a68dc151ef521720": ["france_national"],
    "2a318ec7bcbbcd500e03a967": ["uk_national"],
    "2f8cf6394ae7e9efa66052db": ["uk_national"],
    "d529d2da604c96d363e75a3c": ["uk_national"],
    "09cca41b8168ed9d5a24eb4b": ["uk_national"],
    "ebe5dcc24b16fa1bced5681f": ["india_grouped_aid"],
    "3a80dd72f6aaf1ae9f16fe41": ["india_grouped_aid"],
    "fe4addd5b5223c89cd9cd4f6": ["india_grouped_aid"],
    "81600bd95243d423eedb6c5a": ["india_peer_revision"],
    "92d54cfbbaf73f19dab46c3b": ["brazil_initial_or_self"],
    "90e4996977655de5ddb7bee4": ["brazil_initial_or_self"],
    "b2e103ca33ec93e8d675f9dd": ["brazil_initial_or_self"],
    "e7af5f56875a7719eade7dca": ["brazil_peer_revision"],
    "cad89cb5364ec5dfab413b6c": ["france_central", "uk_central", "india_central", "brazil_central"],
    "1e0423f0520f3badf2794dc2": ["france_central", "uk_central", "india_central", "brazil_central"],
    "43a3b182c86657ed19b511a2": ["capped_synthesis"],
    "0042015270b973ebfef362dc": ["capped_synthesis"],
    "b42da06efee474ba9eb27c41": ["central_synthesis"]
}
