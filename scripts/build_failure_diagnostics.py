"""Freeze small, one-change diagnostic interventions; never amend benchmark cases."""
from copy import deepcopy
import argparse
from pathlib import Path

from country_persona.action_eval import validate_case
from country_persona.io import digest, read_jsonl, sha256, write_json, write_jsonl


ACTION_IDS = ["43cabbaa4d1c8898547e0f92", "11a6f6e8b3e105a875a847ca",
              "9572de56abd38603c867a0e7", "f0ffe7d64cdfa7cb984f1eb3"]
POLICY_IDS = ["c38042eddde9d1ef2cbca5cc", "ac1e72a1d2b7c03758ad7237",
              "7f61e110dae98dac7bec78e1", "70380b733032cf5c3eda9512"]
COUNTRIES = {"IND": "India", "BRA": "Brazil", "FRA": "France"}
WARNING = " A means a recorded vote abstention, not model uncertainty."
CHARACTERS = "Return exactly one character: Y for Yes, N for No, or A for Abstain."


def build(pack, output):
    if output.exists():
        raise ValueError("Choose a fresh diagnostic pack directory")
    parents = {c["id"]: c for c in read_jsonl(pack / "cases.jsonl")}
    cases, design = [], []
    for parent_id in ACTION_IDS:
        parent = parents[parent_id]
        validate_case(parent)
        assert parent["condition"] == "B" and parent["task"] == "recorded_vote_prediction"
        cases.append(parent)
        design.append({"id": parent_id, "parent_id": parent_id, "variant": "baseline_replay"})
        for variant in ["full_country_name", "clarify_vote_target", "remove_abstention_warning", "word_labels"]:
            c = deepcopy(parent)
            if variant == "full_country_name":
                for m in c["prompt"]:
                    m["content"] = m["content"].replace(f"Country: {parent['country']}", f"Country: {COUNTRIES[parent['country']]}")
            elif variant == "clarify_vote_target":
                c["prompt"][0]["content"] += (
                    " Y and N refer to adopting the supplied draft as a whole. They do not label "
                    "approval or disapproval of actions described or condemned inside it. "
                    "Choose the recorded vote category for this draft.")
            elif variant == "remove_abstention_warning":
                assert WARNING in c["prompt"][0]["content"]
                c["prompt"][0]["content"] = c["prompt"][0]["content"].replace(WARNING, "")
            else:
                assert CHARACTERS in c["prompt"][0]["content"]
                c["prompt"][0]["content"] = c["prompt"][0]["content"].replace(
                    CHARACTERS, "Return exactly one word: FAVOR for a Yes vote, AGAINST for a No vote, or ABSTAIN for an abstention.")
                c["prompt"][0]["content"] = c["prompt"][0]["content"].replace(
                    " A means a recorded vote abstention", " ABSTAIN means a recorded vote abstention")
                c["task"] = "diagnostic_vote_words"
            c.pop("case_sha256"); c.pop("id")
            c.update(parent_id=parent_id, diagnostic_variant=variant,
                     evaluation_status="targeted_development_intervention_not_benchmark")
            c["id"] = digest(c)[:24]
            c["case_sha256"] = digest(c)
            validate_case(c)
            cases.append(c)
            design.append({"id": c["id"], "parent_id": parent_id, "variant": variant})
    for parent_id in POLICY_IDS:
        c = deepcopy(parents[parent_id])
        validate_case(c)
        c["prompt"][0]["content"] += (
            " For each substantive source-specific claim, include a short exact supporting quote "
            "from the supplied statement. Omit details that the supplied statement does not establish. "
            "Preserve explicit time qualifiers. Keep the whole answer, including quotes, within 180 words.")
        c.pop("case_sha256"); c.pop("id")
        c.update(parent_id=parent_id, diagnostic_variant="quote_bound_policy",
                 evaluation_status="targeted_development_intervention_not_benchmark")
        c["id"] = digest(c)[:24]; c["case_sha256"] = digest(c)
        validate_case(c)
        cases.append(c)
        design.append({"id": c["id"], "parent_id": parent_id, "variant": "quote_bound_policy"})
    assert len(cases) == len({c["id"] for c in cases}) == 24
    output.mkdir(parents=True)
    write_jsonl(output / "cases.jsonl", cases)
    write_json(output / "manifest.json", {
        "purpose": "Diagnose selected failures with one prompt intervention at a time; no new training or evidence.",
        "status": "frozen_before_diagnostic_inference", "cases": len(cases),
        "parent_pack_sha256": sha256(pack / "manifest.json"),
        "parent_cases_sha256": sha256(pack / "cases.jsonl"),
        "planned_model_lock_sha256": sha256("configs/posttraining/model.lock.json"),
        "files_sha256": {"cases.jsonl": sha256(output / "cases.jsonl")},
        "design": design,
        "hypotheses": {
            "full_country_name": "Country-code encoding may affect the recorded action.",
            "clarify_vote_target": "The model may confuse voting on the draft with attitudes to acts described inside it.",
            "remove_abstention_warning": "The warning distinguishing abstention from uncertainty may suppress the abstention category.",
            "word_labels": "Single-letter verbalization may distort the decision relative to semantic labels.",
            "quote_bound_policy": "Explicit claim-to-source quotations may reduce unsupported detail and recover omitted qualifications."
        },
        "limits": ["Selected after inspecting failures; this is diagnosis, not an unbiased new benchmark.",
                   "One greedy run per input; changed outputs alone do not reveal internal reasoning.",
                   "Word labels are multi-token; canonical Y/N/A probabilities are not reported for that format.",
                   "No post-vote statements or gold votes enter any diagnostic prompt."]})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=Path("data/prepared/eval-pilot-20260927/two-event-v1"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.pack, args.output)
