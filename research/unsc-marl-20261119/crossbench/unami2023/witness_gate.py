"""Check necessary textual prerequisites before awarding witness-based credit."""
from collections import Counter
import json
import re

import judge as prior
import witness_judge as witness

CHECKED = {"consult", "deliverable", "recommend"}


def has(pattern, text):
    return bool(re.search(pattern, text, re.I))


def has_binding(field, text):
    """Find a transparent positive proof form. Absence triggers review."""
    if field == "consult":
        clause = re.search(r"\bconsult(?:ed|ing|ation with|ations (?:with|include))?\b[^.;!?]*", text, re.I)
        return bool(clause and has(r"\bIraq\b", clause[0]) and has(r"\bKuwait\b", clause[0])
                    and has(r"\b(?:UN agencies|Member States|regional organizations|independent experts|civil society)\b",
                            clause[0])
                    and not has(r"\b(?:not|without|exclud\w+|except|omitt\w+)\b", clause[0]))
    if field == "deliverable":
        return (has(r"\b31 March 2024\b", text)
                and has(r"\bindependent strategic review\b", text)
                and has(r"\bSecretary[ -]General\b[^.;!?]*\b(?:conduct|undertake|prepare)\b", text)
                and has(r"\b(?:submit|provide|deliver|transmit)\b[^.;!?]{0,60}\bto the (?:Security )?Council\b", text)
                and not has(r"\b(?:not|instead|never|rather than)\b", text))
    return (has(r"\b(?:relevance|continued relevance)\b", text)
            and has(r"\brecommend(?:ing|ations?)?\b[^.;!?]{0,60}\b(?:mandate|structure|staffing)\b", text)
            and not has(r"\b(?:not|without|instead|never)\b", text))


def gate(row):
    if row["verdict"] != "supported" or row["field"] not in CHECKED:
        return row["verdict"]
    return "supported" if any(has_binding(row["field"], text) for _, _, text in row["windows"]) else None


def controls():
    # Complete or deliberately inadequate candidate clauses. The last case
    # deliberately tests a lexical hit in a counterfactual, with no new fit.
    return (
        ("consult-positive", "consult", "The review must consult Iraq, Kuwait and civil society.", True),
        ("consult-distractor", "consult", "The review must consult Iraq and UN agencies. Kuwait supported the extension.", False),
        ("consult-exclusion", "consult", "The review must consult Iraq and civil society, excluding Kuwait.", False),
        ("consult-paraphrase", "consult", "The review must seek the views of Iraq, Kuwait and civil society.", True),
        ("review-positive", "deliverable", "The Secretary-General was asked to conduct the independent strategic review and submit it to the Council by 31 March 2024.", True),
        ("review-reversed", "deliverable", "The Council was asked to conduct the independent strategic review and submit it to the Secretary-General by 31 March 2024.", False),
        ("review-bystander", "deliverable", "The Secretary-General was asked to conduct the independent strategic review and submit it to Iraq by 31 March 2024.", False),
        ("recommend-positive", "recommend", "The review was to assess relevance and make recommendations regarding the mandate, structure and staffing.", True),
        ("recommend-evaluation", "recommend", "The review will assess the relevance of the mandate and its staffing.", False),
        ("recommend-counterfactual", "recommend", "If the scope were broader, the review would assess relevance and make recommendations on the mandate.", False),
    )


def run():
    output = json.loads((prior.HERE / "witness-evidence/results.json").read_text())
    groups = {}
    for group, block in output["groups"].items():
        revised = [{**row, "admitted": gate(row)} for row in block["records"]]
        groups[group] = {
            "accepted_wrong": sum(r["admitted"] == "supported" and r["reference"] != "supported" for r in revised),
            "accepted_right": sum(r["admitted"] == "supported" and r["reference"] == "supported" for r in revised),
            "sent_to_review": sum(r["admitted"] is None for r in revised),
            "changed": [{"id": r["candidate"], "field": r["field"], "truth": r["reference"]}
                        for r in revised if r["admitted"] != r["verdict"]],
            "outcomes": dict(Counter(r["admitted"] for r in revised)),
        }
    probes = []
    for key, field, candidate, expected in controls():
        spans = witness.windows(candidate, field)
        accepted = any(has_binding(field, text) for _, _, text in spans)
        probes.append({"id": key, "field": field, "evidence": candidate, "should_allow": expected, "allowed": accepted})
    return {"groups": groups, "binding_controls": probes,
            "scope": "Posthoc requirements for three observed false-credit modes. "
                     "A missing proof form refers a case for review. "
                     "The authored controls include expected failures and do not certify entailment."}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
