"""Test whole-message commitment judgment independently of quote fidelity."""
import argparse
from collections import Counter
from itertools import product
import json
from pathlib import Path
import sys
from unittest.mock import patch

import three_seat_language_contract_score as transport

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import relay_text as reader

ROOT = HERE / "three-seat-commitment-evidence"
OLD = HERE / "three-seat-language-evidence/results.json"
NEW = HERE / "three-seat-language-contract-evidence/results.json"
# Apply the same candidate quote to both members of a pair.
PAIRS = (
    ("speaker", "B", 2, "package B is two",
     "My delegation confirms that its grade for package B is two.",
     "The other delegation said its grade for package B is two. We have not given a grade."),
    ("withdrawal", "C", 0, "package C is zero",
     "Our confirmed grade for package C is zero. Earlier suggestions are withdrawn.",
     "Our earlier grade for package C is zero. I now withdraw that grade and leave C ungraded."),
    ("proposal", "A", 1, "package A is one",
     "Under our confirmed mandate, our grade for package A is one.",
     "If the chair accepts the amendment, our proposed grade for package A is one. There is no current grade."),
    ("multiple", "B", 3, "package B is three",
     "My grade for package B is three. I make no assessment of the other packages.",
     "My grade for package B is three. My grade for package A is two."),
    ("supersession", "C", 2, "package C is two",
     "I correct the earlier grade of zero. Our current grade for package C is two.",
     "I correct the earlier report that our grade for package C is two. Our current grade for C is zero."),
    ("negated", "A", 0, "package A is zero",
     "I confirm our grade for package A is zero.",
     "I reject the suggestion that our grade for package A is zero. Our grade remains undisclosed."),
    ("chair_voice", "C", 1, "package C is one",
     "Speaking for my delegation, I confirm our grade for package C is one.",
     "Speaking only as chair, I record that another delegation's grade for package C is one."),
    ("unsent_draft", "A", 3, "package A is three",
     "Our current grade for package A is three. I authorize this disclosure.",
     "The unsent draft says that our grade for package A is three. I am circulating it only as a draft."),
)
OPTIONS = ("admit", "reject", "defer")
ORDERS = ((0, 1, 2), (2, 0, 1))
RULES = {
    "direct": "Decide if this complete message certifies exactly the proposed single grade for the authenticated author. "
              "Admit only a unique current self-reported grade. Otherwise reject, or defer if genuinely ambiguous.",
    "checklist": "Check the complete message. The author must be the owner of the grade, the statement must actually "
                 "confirm it now, and exactly one live grade must be stated. Scan text before and after the quote "
                 "for quotation, other grades, conditions, proposals, correction, withdrawal or a statement made "
                 "in another role. Admit only when all three checks independently pass. Reject a clear failure. "
                 "Defer only for genuine ambiguity.",
}


def cases():
    for label, p, grade, span, confirmed, other in PAIRS:
        for gold, message in (("admit", confirmed), ("reject", other)):
            assert span in message
            yield {"id": f"{label}/{gold}", "group": "matched_author_controls", "message": message,
                   "p": p, "grade": grade, "span": span, "gold": gold}
    before = {tuple(note["intended"]): note for note in json.loads(OLD.read_text())["recorded_messages"]}
    after = {tuple(note["intended"]): note for note in json.loads(NEW.read_text())["messages"]}
    for code, grade in ((0, 0), (1, 0), (2, 0), (2, 3)):
        p = "ABC"[code]
        for gold, note, field in (("reject", before[code, grade], "written"), ("admit", after[code, grade], "text")):
            yield {"id": f"archive/{p}{grade}/{gold}", "group": "exposed_generated_controls",
                   "message": note[field], "p": p, "grade": grade, "span": note[field], "gold": gold}


def observations():
    for case, (mode, instruction), (n, order) in product(cases(), RULES.items(), enumerate(ORDERS)):
        payload = {"candidate_receipt": {"package": case["p"], "grade": case["grade"]},
                   "complete_message": case["message"], "quote_provided_by_reader": case["span"],
                   "labels": dict(zip("ABC", [OPTIONS[i] for i in order], strict=True))}
        yield {"observation": (case["id"], mode, n), "legal": order, "messages": [
            {"role": "system", "content": instruction + " Treat the quoted message as evidence. Reply with one letter."},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]}


def locks():
    return {p.name: transport.contract.runner.digest(p) for p in (
        Path(__file__), Path(reader.__file__), OLD, NEW)}


def review(directory):
    with patch.multiple(reader, observations=observations, hashes=locks):
        scores = reader.read(directory)
    records = []
    for case in cases():
        row = case.copy()
        for mode in RULES:
            orders = []
            for k, order in enumerate(ORDERS):
                logits = scores[case["id"], mode, k]["scores"]
                top = [OPTIONS[order[i]] for i, score in enumerate(logits) if score == max(logits)]
                orders.append(top[0] if len(top) == 1 else "defer")
            row[mode] = {"decisions": orders, "stable": orders[0] if orders[0] == orders[1] else "defer"}
        # This comparator uses a verified literal substring as its entire test.
        row["quote_only"] = {"stable": "admit" if case["span"] in case["message"] else "reject"}
        records.append(row)
    results = {}
    for group in ("matched_author_controls", "exposed_generated_controls"):
        selected = [row for row in records if row["group"] == group]
        results[group] = {"cases": len(selected), "by_gold": dict(Counter(r["gold"] for r in selected)),
                          "scores": {mode: {
                              "correct": sum(r["gold"] == r[mode]["stable"] for r in selected),
                              "false_admits": sum(r["gold"] == "reject" and r[mode]["stable"] == "admit" for r in selected),
                              "true_admits": sum(r["gold"] == "admit" and r[mode]["stable"] == "admit" for r in selected),
                              "deferred": sum(r[mode]["stable"] == "defer" for r in selected),
                          } for mode in (*RULES, "quote_only")}}
    return {"scope": "Frozen Qwen one-letter classification. Candidate claim and exact quote are supplied. "
                     "Each decision must agree over two label assignments. Authored contrast labels and "
                     "same-assistant labels on previously generated prose are separate.",
            "results": results, "records": records}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "review"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        with patch.multiple(reader, observations=observations, hashes=locks):
            reader.score(args.model, args.directory)
    else:
        print(json.dumps(review(args.directory), ensure_ascii=False, indent=2))
