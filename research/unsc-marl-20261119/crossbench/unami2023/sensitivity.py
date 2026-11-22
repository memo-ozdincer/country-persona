"""Rescore partial criteria without changing the frozen endpoint or guard."""
import json

from judge import FINAL_TEXT, reviewed

# A partial witness meets one of two named clauses in an otherwise failed
# criterion. Lists are fixed by same-assistant reading of this output set.
PARTIAL = {
    "pooled_solo": {
        "vote": ("resolution adoption", "adopt resolution 2682 (2023)"),
        "support": ("dialogue or reconciliation", "advice on inclusive political dialogue and reconciliation"),
        "participation": ("women's participation", "participation of women"),
        "deliverable": ("independent review and deadline", "independent strategic review of UNAMI by 31 March 2024"),
        "consult": ("non-state or multilateral consultation", "UN agencies, Member States, regional organizations"),
    },
    "independent_drafts": {
        "vote": ("resolution adoption", "adopted unanimously Resolution 2682 (2023)"),
        "support": ("dialogue or reconciliation", "prioritize inclusive political dialogue and reconciliation"),
        "participation": ("women's participation", "participation of women"),
        "deliverable": ("independent review and deadline", "independent strategic review was mandated to conclude by 31 March 2024"),
    },
    "interactive": {
        "tally": ("affirmative tally", "the Council voted 15 in favour"),
        "support": ("dialogue or reconciliation", "advice on inclusive political dialogue and reconciliation"),
        "participation": ("women's participation", "participation of women"),
        "deliverable": ("independent review and deadline", "independent strategic review of UNAMI is mandated to conclude no later than 31 March 2024"),
    },
}


def run():
    assessments, strict = reviewed()
    final = next(iter(json.loads(FINAL_TEXT.read_text()).values()))
    out = {}
    for i, (path, text) in enumerate(final.items()):
        arm = path.split("/")[-2]
        before = strict[arm]
        for unit, (_, span) in PARTIAL[arm].items():
            assert span in text and assessments[f"record-{i+1}", unit] != "supported"
        out[arm] = {"frozen_score": before["points"], "sensitivity_score": before["points"] + 3.5 * len(PARTIAL[arm]),
                    "guard_clear": before["guard_clear"], "partial_witnesses": PARTIAL[arm]}
    return {"scope": "Retrospective same-assistant partial credit. A named surviving clause earns half credit inside "
                     "the original criterion. Contradictions still fail the material guard. Retain frozen scores for the main comparison.",
            "results": out}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
