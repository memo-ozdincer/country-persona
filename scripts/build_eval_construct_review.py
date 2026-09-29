"""Prepare versioned policy and source-support review; never invent human ratings."""
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import argparse
import json

from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl
from country_persona.policy_eval import rubric_digest, score_policy_response, summarize_policy_scores

# Splitting conjunctions makes omissions visible. Unchanged criteria retain
# their source-backed v1 definitions; these are proposed, not human-approved.
ATOMIC = {
    "climate-fra": {
        "beyond_military": [
            ("military_insufficient", "Explain that armed forces and peacekeepers alone are insufficient."),
            ("climate_crisis_links", "Include understanding the links between climate change and crises as part of a longer-term response."),
            ("resilience", "Include strengthening the resilience of States or their populations as part of that response.")],
    },
    "climate-ind": {
        "institution": [
            ("preferred_forum", "Identify UNFCCC/COP as India's preferred forum for climate issues."),
            ("inclusive_process", "Preserve the importance of an inclusive, consensus-based process with developing-country participation."),
            ("alternative_platform", "Explain India's concern about an alternative Security Council platform.")],
        "qualification": [
            ("acknowledged_harms", "Recognize India's acknowledgement that climate change affects lives and has exacerbated conflicts."),
            ("reject_absolute_denial", "Reject the analyst's claim that India denied every climate–conflict connection; an explicit corrective contrast is sufficient.")],
        "causality": [
            ("reductionism", "Explain India's objection to reducing conflicts to a climate-only explanation or oversimplifying their causes."),
            ("attributed_argument", "Attribute the contested causal/security-link argument to India; do not present it as a settled scientific conclusion.")],
    },
    "climate-gbr": {
        "reporting": [
            ("un_reporting", "Include support for comprehensive UN reporting on climate/security links."),
            ("council_role", "Include the Security Council among the UN bodies with a role.")],
    },
    "climate-bra": {
        "mandates": [
            ("unfccc_forum", "Identify the inclusive UNFCCC forum as Brazil's preferred venue."),
            ("respect_mandates", "Include respect for institutional mandates or avoiding duplication."),
            ("avoid_reallocation", "Explain Brazil's objection to reallocating the climate agenda to the Security Council.")],
        "finance": [
            ("finance_direction", "Identify developed-country finance supporting developing countries as a practical priority."),
            ("finance_delivery", "Include scaling up and timely delivery of that financing."),
            ("existing_commitments", "Connect the financial flows to existing commitments or enhanced climate action.")],
    },
    "ukraine-fra": {
        "support": [
            ("continued_support", "Report France's commitment to continuing support for Ukraine."),
            ("support_duration", "Preserve 'for as long as necessary' or a substantively equivalent duration qualifier."),
            ("support_purpose", "Link that support to Ukraine's independence, sovereignty and territorial integrity; an equivalent umbrella formulation is acceptable.")],
    },
    "ukraine-gbr": {
        "rejection": [
            ("illegitimate_referendums", "Describe the UK's rejection of the referendums as illegal, illegitimate or coercive."),
            ("sovereignty", "Connect that rejection to Ukraine's sovereignty or territorial integrity.")],
    },
    "ukraine-ind": {
        "diplomacy": [
            ("cease_hostilities", "Include an immediate cessation of hostilities."),
            ("negotiations", "Include dialogue, diplomacy or return to negotiations.")],
        "principles": [
            ("legal_order", "Include international law or the UN Charter as a principle."),
            ("sovereign_integrity", "Include sovereignty and territorial integrity.")],
        "human_effects": [
            ("ukraine_assistance", "Include India's humanitarian assistance to Ukraine."),
            ("global_south_support", "Include economic support to neighbours in the global South; substituting a narrower region is insufficient unless the original scope is also preserved."),
            ("cost_channels", "Include food, fuel and fertilizer costs as concrete channels of economic distress.")],
    },
    "ukraine-bra": {
        "conditional": [
            ("possible_legitimacy", "Acknowledge self-determination and the possibility that referendums can legitimately express it."),
            ("conditional_validity", "Explain that legitimacy depends on conditions rather than automatically following from the use of a referendum.")],
        "conditions": [
            ("free_will_under_conflict", "Include Brazil's concern that people in conflict areas cannot be assumed able to express their will freely."),
            ("procedural_condition", "Include at least one of transparency, freedom of expression or independent monitoring; this alone does not settle every condition.")],
        "current_concern": [
            ("current_referendums", "Describe Brazil's negative assessment of the current referendums."),
            ("integrity_or_negotiation", "Include territorial integrity or a ceasefire/negotiation commitment.")],
    },
}

BOUNDARIES = {
    "climate-fra": "Saying 'deploy peacekeepers' alone omits the insufficiency qualification and the longer-term response.",
    "climate-ind": "Rejecting a Council platform is compatible with acknowledging climate harms; do not score either as total denial.",
    "climate-gbr": "Support for this draft does not establish support for Council-imposed national carbon quotas.",
    "climate-bra": "Caution about a security framing is not denial of climate-related tensions or displacement.",
    "ukraine-fra": "The selected passage specifies duration and purpose, but not 'financial and military' assistance types or an exact pledge amount.",
    "ukraine-gbr": "An announced call to support a draft on 27 September is not itself the 30 September vote record.",
    "ukraine-ind": "Humanitarian aid, global-South economic support and food/fuel/fertilizer effects are distinct units. 'South Asia' alone narrows the supplied scope.",
    "ukraine-bra": "Adding independent monitors and transparent counting does not by itself satisfy the separate freedom-under-conflict condition.",
}

CLAIMS = {
    "climate-fra": [
        ("supported", "France supported a Security Council role in anticipating and preventing climate-related security risks.", "The Security Council must be able to anticipate, prevent and seek solutions to counter the effects of climate change"),
        ("contradicted", "France said armed forces and peacekeepers alone were sufficient for a long-term response.", "we cannot rely solely on the commitment of the armed forces and peacekeepers")],
    "climate-ind": [
        ("supported", "India argued against an alternative climate platform outside the established inclusive process.", "Let us not deviate from an established and inclusive process of decision-making"),
        ("contradicted", "India denied that climate change had ever exacerbated any conflict.", "While we recognize the fact that climate change has impacted the lives of people and exacerbated conflicts in many places")],
    "climate-gbr": [
        ("supported", "The UK explicitly supported the draft resolution submitted to the Council.", "Therefore, we support the draft resolution submitted to the Council as an important first step."),
        ("not_established", "The UK approved binding national carbon quotas imposed by the Security Council.", None)],
    "climate-bra": [
        ("supported", "Brazil called for timely and increased developed-country financing for developing countries affected by climate change.", "The mobilization, scaling-up and timely delivery of financing by developed nations are the need of the hour"),
        ("contradicted", "Brazil said reallocating the climate agenda to the Security Council was a better use of effort than financing existing commitments.", "The time and energy diverted to reallocate the climate agenda to the Security Council would be better spent in fostering financial flows")],
    "ukraine-fra": [
        ("supported", "France committed to supporting Ukraine for as long as necessary.", "France will continue to provide Ukraine with the support it needs for as long as is necessary"),
        ("not_established", "France specified an exact ten-billion-euro financial pledge in this statement.", None)],
    "ukraine-gbr": [
        ("supported", "The UK urged support for the draft brought forward by the United States and Albania.", "support the draft resolution the United States and Albania have brought forward today."),
        ("not_established", "The 27 September statement itself records the UK's eventual vote on 30 September.", None)],
    "ukraine-ind": [
        ("supported", "India called for an immediate cessation of hostilities and dialogue or diplomacy.", "India has repeatedly called for an immediate cessation of hostilities"),
        ("not_established", "The supplied 27 September statement explicitly records India abstaining in the later 30 September vote.", None)],
    "ukraine-bra": [
        ("supported", "Brazil described the validity of referendums as conditional.", "Its validity, however, depends on certain conditions."),
        ("contradicted", "Brazil said populations in conflict areas could reasonably be assumed able to express their will freely.", "It is unreasonable to assume that populations in areas in conflict are able to freely express their will.")],
}


def support_span(evidence, quote):
    start = evidence["text"].index(quote)
    if evidence["text"].count(quote) != 1:
        raise ValueError("Ambiguous source anchor")
    return {"evidence_id": evidence["id"], "start": start, "end": start + len(quote),
            "quote": quote, "text_digest": evidence["text_digest"]}


def build(pack, outputs, destination):
    if destination.exists():
        raise ValueError("Choose a fresh construct review directory")
    original_manifest = json.loads((pack / "manifest.json").read_text())
    for name in ("cases.jsonl", "policy.references.jsonl", "evidence.jsonl", "action.references.jsonl"):
        if sha256(pack / name) != original_manifest["files_sha256"][name]:
            raise ValueError("Frozen source pack changed")
    all_cases = list(read_jsonl(pack / "cases.jsonl"))
    cases = {c["id"]: c for c in all_cases}
    evidence = {e["id"]: e for e in read_jsonl(pack / "evidence.jsonl")}
    refs = list(read_jsonl(pack / "policy.references.jsonl"))
    for ref in refs:
        ref["rubric_version"] = "atomic-v2-proposed-independent-review-pending"
        old_criteria = ref["criteria"]
        new = []
        for criterion in old_criteria:
            for unit_id, description in ATOMIC[ref["item_key"]].get(criterion["id"], [(criterion["id"], criterion["description"])]):
                unit = deepcopy(criterion)
                unit.update(id=unit_id, description=description, parent_v1_criterion=criterion["id"],
                            support_scope="Read the full bounded statement; inherited spans are navigation anchors, not an automatic entailment test.")
                new.append(unit)
        ref["criteria"] = new
        ref["universal_checks"]["all_material_claims_supported"] = (
            "Every substantive assertion attributed to the supplied source must be supported by that bounded source. "
            "Clearly marked inference is allowed only when it does not contradict the source or invent a commitment. "
            "Quotation alone does not establish claim entailment. A quotation of a claim being rejected is not endorsement.")
        ref["reference_notes"] += [BOUNDARIES[ref["item_key"]],
            "All listed units are required; alternatives are allowed only where explicitly written. Accept equivalent paraphrases.",
            "A factual assertion absent from this packet is not automatically false in the wider world; score its unsupported attribution."]
        ref["rubric_sha256"] = rubric_digest(ref)
    ref_index = {r["id"]: r for r in refs}
    predictions = [p for p in read_jsonl(outputs) if p["task"] == "policy_fidelity"]
    if {p["id"] for p in predictions} != set(ref_index):
        raise ValueError("Expected all 16 original policy outputs")
    templates, unreviewed = [], []
    deck = ["# Actual model outputs: proposed atomic rubric v2", "",
            "No human ratings have been supplied. This is a rubric revision after exposed development errors, not an independent validation.", "",
            "Rate independently before seeing the other reviewer's ratings. Use met/unmet/unratable for every unit and check. "
            "An uncertain source or ambiguous requirement is unratable with an explanation. Accept equivalent paraphrases. "
            "Do not infer votes from uncertainty. Empty answers fail. This deck hides arm/model labels; source citations may still reveal the arm.", "",
            "The full source passage is the reference for both arms. Unsupported means unsupported by that bounded reference, even if true elsewhere. "
            "No criterion-level score is a calibrated claim-level factuality rate. Report individual required units and whole-response pass separately.", ""]
    for pred in sorted(predictions, key=lambda p: p["response_id"]):
        ref, case = ref_index[pred["id"]], cases[pred["id"]]
        template = {"id": case["id"], "case_sha256": case["case_sha256"], "response_id": pred["response_id"],
                    "output_digest": digest(pred["output"]), "rubric_sha256": ref["rubric_sha256"],
                    "reviewer_id": None, "reviewer_kind": None,
                    "criteria": {c["id"]: None for c in ref["criteria"]},
                    "checks": {k: None for k in ref["universal_checks"]}, "notes": None}
        templates.append(template)
        unreviewed.append(score_policy_response(case, ref, pred))
        # The question is identical within the pair; remove any attached evidence
        # from the question view and supply the same reference passage below.
        question = case["prompt"][1]["content"].split("DATED PUBLIC STATEMENT")[0]
        deck += [f"## Response {pred['response_id']}", "", question, "", "### Answer", "", pred["output"], "",
                 "### Reference source", "", evidence[ref["item_key"]]["text"], "", "### Required units", ""]
        deck += [f"- `{c['id']}`: {c['description']}" for c in ref["criteria"]]
        deck += ["", "### Checks", ""] + [f"- `{k}`: {v}" for k, v in ref["universal_checks"].items()]
        deck += ["", "### Boundary example", "", BOUNDARIES[ref["item_key"]], ""]
    # Draft source-support labels: these do not change historical vote gold.
    action_annotations = []
    for ref in read_jsonl(pack / "action.references.jsonl"):
        case = cases[ref["id"]]
        supplied = case["evidence_ids"]
        announced = case["condition"] == "B" and case["country"] == "GBR"
        action_annotations.append({"id": case["id"], "case_sha256": case["case_sha256"],
            "observed_vote_reference_unchanged": True,
            "dated_speech_relationship": "explicit_draft_support" if announced else "policy_context_only" if supplied else "no_dated_speech_supplied",
            "later_recorded_vote_explicitly_established_by_prior_speech": False if supplied else None,
            "proposal_metadata_may_include_sponsorship": True,
            "annotation_scope": "The selected prior speech, not a claim that the whole packet lacks predictive clues.",
            "evidence_ids": supplied, "reviewer_kind": "assistant", "independent_review": "pending"})
    source_cases, source_refs = [], []
    for key, claims in CLAIMS.items():
        e = evidence[key]
        for label, claim, quote in claims:
            case = {"task": "bounded_source_entailment", "country": e["country"],
                    "evidence_id": key, "source_text_digest": e["text_digest"], "claim": claim,
                    "instruction": "Using only the supplied statement, mark the assertion as supported, contradicted, or not established. "
                                   "Not established means the statement neither supports nor contradicts it. It is not a recorded vote abstention.",
                    "source_text": e["text"], "provenance": "assistant_authored_claim_about_observed_source"}
            case["id"] = digest(case)[:24]; case["case_sha256"] = digest(case)
            source_cases.append(case)
            source_refs.append({"id": case["id"], "case_sha256": case["case_sha256"], "proposed_label": label,
                                "support_spans": [support_span(e, quote)] if quote else [],
                                "bounded_absence_scope": key if quote is None else None,
                                "reviewer_kind": "assistant", "independent_review": "pending"})
    destination.mkdir(parents=True)
    write_jsonl(destination / "policy.references.v2.jsonl", refs)
    write_jsonl(destination / "review-template.v2.jsonl", templates)
    write_jsonl(destination / "source-support.annotations.jsonl", action_annotations)
    write_jsonl(destination / "source-entailment.cases.jsonl", source_cases)
    write_jsonl(destination / "source-entailment.proposed-references.jsonl", source_refs)
    (destination / "review-deck.v2.md").write_text("\n".join(deck))
    report = {"status": "assistant_prepared_independent_review_pending", "created_at": datetime.now(timezone.utc).isoformat(),
              "source_pack_sha256": sha256(pack / "manifest.json"), "model_outputs_sha256": sha256(outputs),
              "builder_sha256": sha256(__file__), "policy_responses": len(predictions),
              "distinct_policy_questions": len({r["item_key"] for r in refs}),
              "required_units_per_question": {r["item_key"]: len(r["criteria"]) for r in refs},
              "source_entailment_claims": len(source_cases), "action_support_annotations": len(action_annotations),
              "unreviewed_summary": summarize_policy_scores(unreviewed),
              "independent_reviewers": 0, "inter_rater_agreement": None,
              "changes": ["Split selected compound criteria into separately visible omissions; parent v1 IDs retained.",
                          "Require support for every substantive source assertion, not only explicit commitments.",
                          "Bind ratings to the rubric version as well as exact case and response text.",
                          "Separate stated policy/announced support from evidence of the subsequent vote."],
              "limits": ["v2 scores would use a different criterion denominator; do not compare them directly to v1.",
                         "Unknown or unreviewed semantic labels are not an evaluator accuracy estimate.",
                         "The examples were authored after inspecting failures; an independent sample is required."]}
    report["files_sha256"] = {p.name: sha256(p) for p in destination.iterdir() if p.is_file()}
    write_json(destination / "manifest.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=Path("data/prepared/eval-pilot-20260927/two-event-v1"))
    parser.add_argument("--outputs", type=Path, default=Path("runs/two-event-996664-base-v1/predictions.jsonl"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.pack, args.outputs, args.output)
    print(json.dumps({k: result[k] for k in ("status", "required_units_per_question", "unreviewed_summary")}, indent=2))
