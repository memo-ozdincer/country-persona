"""Audit whether a targeted judge reward favors faithful text over a flawed edit."""
import json

from minurso_atomic_controls import TARGETS
from minurso_atomic_judge import ANCHORS
from minurso_atomic_review import digest

EVIDENCE = ANCHORS.parent.parent / "evidence"
FILES = {
    "joint_judgment": EVIDENCE / "source-record-minurso-atomic-controls/score.json",
    "candidate_only": EVIDENCE / "source-record-minurso-candidate-fields/score.json",
}


def report():
    result = {}
    for name, path in FILES.items():
        data = json.loads(path.read_text())
        rows = {(r["candidate"], r.get("field", r.get("part"))): r for r in data["outcomes"]}
        decide = "agreement" if name == "joint_judgment" else "consensus"
        pairs = []
        for edit, fields in TARGETS.items():
            if edit == "anchor-base":
                continue
            target, unchanged = fields
            correct = rows["anchor-base", target]
            flawed, invariant = rows[edit, target], rows[edit, unchanged]
            assert correct["truth"] == invariant["truth"] == 1 and flawed["truth"] != 1
            before, after = int(correct[decide] == 1), int(flawed[decide] == 1)
            pairs.append({"edit": edit, "target": target, "original": before, "edited": after,
                          "unchanged_supported": invariant[decide] == 1})
        result[name] = {
            "sha256": digest(path), "pairs": pairs,
            "faithful_strictly_rewarded_more": sum(r["original"] > r["edited"] for r in pairs),
            "flawed_still_rewarded": sum(r["edited"] for r in pairs),
            "unchanged_supported": sum(r["unchanged_supported"] for r in pairs),
        }
    return {
        "scope": "Posthoc one-point reward audit using the unanimous verdict on a single edited field. "
                 "No policy was fitted and no complete record was released on these checks.",
        "methods": result,
    }


if __name__ == "__main__":
    print(json.dumps(report(), indent=2))
