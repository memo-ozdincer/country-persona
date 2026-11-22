"""Replay an explicit exclusion check and diagnose exact-quote recall."""
from hashlib import sha256
import json
from pathlib import Path
import re

import request_witness as witness
import witness_replay as replay

HERE = witness.HERE
NEW_EXCLUSION = re.compile(
    r"\b(?:do not (?:get|retrieve|return|need|include|want)|don't (?:get|retrieve|return|need|include|want)|"
    r"skip|ignore|omit|already (?:have|hold|received|possess))\b",
    re.I,
)
SENTENCE_BOUNDARY = re.compile(r"(?<!\b[A-Z]\.[A-Z]\.)(?<=[.!?])\s+")
REFERENCE_SPANS = {
    "reserve/notification_excludes_national": "the result letter",
    "reserve/national_excludes_notification": "the case Indonesia made as sponsor",
    "reserve/notification_with_actor": "communication gave delegates the certified voting outcome",
    "reserve/national_only": "the American delegate's explanation of why her country opposed the draft",
    "reserve/both_roles": "what Djani argued as Indonesia's representative\nthe message he later sent as Council President",
    "fresh/separate_artifacts": "the Indonesian sponsor's explanation\nthe letter reporting the completed ballot",
    "fresh/either_delegation": "from Russia\nfrom the United States",
    "new/two_voices": "the Indonesian sponsor's policy case\nthe Russian delegation's vote explanation",
    "witness/negative_vote": "the explanation of the negative vote",
    "witness/alternative": "the explanation Russia gave for its vote\nthe letter reporting the written result",
}
FRESH_CONTEXTS = {
    "explicit_omission": ("Omit Russia's explanation. Send the United States' explanation.", "Russia's explanation", False),
    "already_collected": ("We already received the American explanation. Find Russia's explanation.",
                          "the American explanation", False),
    "later_positive_clause": ("We already received the American explanation. Find Russia's explanation.",
                              "Russia's explanation", True),
    "negative_with_initials": ("Ignore the U.S. explanation. Send Russia's explanation.", "the U.S. explanation", False),
    "negation_after_object": ("The American explanation is not what I need. Send Russia's explanation.",
                              "The American explanation", False),
    "held_after_object": ("The explanation from Russia is already in my file. Send the American explanation.",
                          "The explanation from Russia", False),
}


def compile_guarded(text, output, ended):
    decision, reason = witness.compile_intent(text, output, ended)
    if not decision or decision[0] == "unspecified":
        return decision, reason
    for span in output.splitlines():
        left = text[:text.index(span)]
        sentence_prefix = SENTENCE_BOUNDARY.split(left)[-1]
        if NEW_EXCLUSION.search(sentence_prefix + span):
            return None, "explicit_exclusion_or_possession"
    return decision, reason


def run():
    archive_path = HERE / "witness-evidence/results.json"
    observed = witness.partner.read(archive_path)["records"]
    cases = {}
    for key, example in observed.items():
        text, raw = example["assignment"], example["generated_spans"]
        trace_result = example["decision"]
        after, reason = compile_guarded(text, raw, example["reason"] != "invalid_generation")
        expected = (example["reference"][0], tuple(example["reference"][1]))
        row = {"old": trace_result, "new": after, "expected": expected, "exact": after == expected, "reason": reason}
        if key in REFERENCE_SPANS:
            spans = REFERENCE_SPANS[key]
            assert all(text.count(span) == 1 for span in spans.splitlines()), key
            alternate, why = compile_guarded(text, spans, True)
            row["manual_witness_replay"] = {"spans": spans, "decision": alternate,
                                            "reason": why, "exact": alternate == expected}
        cases[key] = row
    validation = {}
    for key, (text, spans, expected) in {**replay.FOILS, **FRESH_CONTEXTS}.items():
        first, _ = witness.compile_intent(text, spans, True)
        after, why = compile_guarded(text, spans, True)
        old, new = [bool(value and value[0] != "unspecified") for value in (first, after)]
        validation[key] = {"text": text, "supplied_spans": spans, "expected_admission": expected,
                           "prior_admission": old, "new_admission": new, "reason": why}
    return {"scope": "Add a syntactic pre-object exclusion and already-held check to the existing exact-span gate. "
                     "All proposed quotes come from archived model outputs or the explicitly labeled manual diagnostics. "
                     "A human can supply better spans, but shared wording and unsupported role cues still challenge the grammar.",
            "code_sha256": sha256(Path(__file__).read_bytes()).hexdigest(), "witness_sha256": sha256(archive_path.read_bytes()).hexdigest(),
            "model_cases": cases, "context_controls": validation}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
