"""Check exact spans and separate certified dispositions from reason quality."""
import json
from pathlib import Path

import three_seat_memo as direct
import three_seat_proof_memo as proof

HERE = Path(__file__).resolve().parent
LABELS = {
    "direct": {
        "d_before": ("false", "eliminating their first card", "The receipt selects the first card."),
        "d_with_reply": ("false", "D at 1", "The second receipt gives A a grade of one."),
        "shared_before": ("false", "Only Package D remains viable", "The first seat rules out D."),
        "impasse_with_reply": ("false", "Only Package D remains viable", "The first seat rules out D."),
        "f_with_reply": ("false", "Package F (grade 2 vs 2)", "Positive grades satisfy the feasibility threshold."),
        "still_unresolved": ("false", "only Package A as the sole compatible winner", "A and D each win a completion."),
    },
    "verified_proof": {
        "d_before": ("adequate", "feasible outcomes exist for both A and D", "Both winners occur in completions."),
        "d_with_reply": ("incomplete", "while Package A is feasible", "The reason omits D's advantage on the lowest grade."),
        "shared_before": ("incomplete", "fails to meet the threshold for a common winner",
                          "The reason omits the contrast between impasse and F."),
        "impasse_with_reply": ("false", "a total grade exceeding the threshold for any package",
                               "A zero in any seat excludes each package."),
        "f_with_reply": ("incomplete", "leaving F as the only compatible world",
                         "F is a package. The preceding sentence correctly establishes its feasibility."),
        "still_unresolved": ("adequate", "Package D wins in one scenario and Package A in another",
                             "The possible worlds have no common winner."),
    },
}


def run():
    original = direct.score(direct.ROOT)
    guided = proof.score(proof.ROOT)
    keys = {row["id"]: row for row in direct.requests()}
    results = {}
    for group, data in (("direct", original), ("verified_proof", guided)):
        rows = []
        assert {row["id"] for row in data["records"]} == LABELS[group].keys()
        for r in data["records"]:
            key = keys[r["id"]]
            status, span, issue = LABELS[group][r["id"]]
            assert span in r["reason"] or span in r["decision"]
            rows.append({**r, "reason_status": status, "witness": span, "review": issue,
                         "possible_worlds": [{"cards": w, "winners": sorted(direct.game.TRUTH[w])}
                                             for w in key["possible"]]})
        results[group] = {"correct_first_line": sum(r["correct"] for r in rows),
                          "adequate_and_correct": sum(r["correct"] and r["reason_status"] == "adequate" for r in rows),
                          "records": rows}
    return {"scope": "Six paired views. Decisions are machine scored, with same-assistant exact-span review "
                     "of reason quality. The proof arm supplies the verified disposition and changes the task wording.",
            "results": results}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
