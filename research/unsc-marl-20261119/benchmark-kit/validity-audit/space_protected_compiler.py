"""Render verified May procedure separately from archived national prose."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import space_protected_review as review

bank, study, judge = review.bank, review.study, review.judge


def compile_records(directory, annotations):
    originals = review.interpret(directory, annotations)
    notes = bank.archived()
    comparison_record = originals["team-3"]
    comparison = comparison_record["selected_candidate_spans"]["open-issues"][-1]
    assert comparison.startswith("While both nations acknowledged")
    assert comparison in comparison_record["selected_candidate_spans"]["overlap"]
    later = bank.guard.LEDGER[3].replace("Standalone draft ", "Standalone ")
    results = dict(originals)
    for mask in range(8):
        japan, china, may = (bool(mask & (1 << i)) for i in range(3))
        parts, units = [], dict(review.PUBLIC_UNITS)

        def add(text):
            parts.append(text)
            return len(judge.sentence_rows("\n\n".join([bank.PUBLIC, *parts])))

        if japan:
            jp = add(notes[study.FIELDS[0]])
            units[4] = ["M", [2, 5, jp], [1, 2, 5]]
        if china:
            cn = add(notes[study.FIELDS[1]])
            units[3] = ["M", [1, cn], [1, 4]]
            units[5] = ["M", [2, 5, cn], [1, 2, 4]]
        if japan and china:
            both = add(comparison)
            units[2] = ["?", [3, jp, cn, both], [2, 4, 5]]
            units[6] = ["M", [jp, cn, both], [2, 4, 5]]
            units[7] = ["M", [jp, cn, both], [4, 5]]
        if may:
            stage = add(later)
            units[8] = ["M", [stage], [3]]
        body = "\n\n".join(parts)
        answer = "\n\n".join(filter(None, [bank.PUBLIC, body]))
        verdict = {"units": [units.get(i, review.OMITTED) for i in range(10)], "guard": ["C", [], []]}
        assessment = judge.interpret(f"compiled-{mask}", answer, verdict)
        score = assessment["score"]["final"]["lower"]
        words = len(body.split())
        assert words <= bank.BODY_WORDS and len(judge.sentence_rows(bank.PUBLIC)) == 6
        label = f"team-{mask}"
        results[label] = {
            "answer": answer, "body_words": words, "source_ids": originals[label]["source_ids"],
            "points": score, "release_points": score, "eligible": True, "strict_complete": score == 70,
            "composition": {"may_procedure": "verified ledger entry" if may else None,
                            "national_notes": [f for bit, f in zip((1, 2), study.FIELDS) if mask & bit],
                            "comparison_source": "team-3 final body" if japan and china else None},
            **assessment,
        }
    return results


def report(directory, annotations, exact):
    rows = compile_records(directory, annotations)
    original = json.loads((directory / "score.json").read_text())
    with patch.object(review, "interpret", return_value=rows):
        content = review.report(directory, annotations, exact)
    return {**content, "scope": "Within-docket compiler using verified May text, exact archived national notes, "
            "and a reviewed model comparison. The router is frozen. Record-assembly result.",
            "compiler_sha256": study.runner.digest(Path(__file__)),
            "original_score_sha256": study.runner.digest(directory / "score.json"),
            "original_team_points": [original["bank"][f"team-{i}"]["points"] for i in range(8)],
            "compiled_team_points": [rows[f"team-{i}"]["points"] for i in range(8)]}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--directory", type=Path, default=bank.OUT)
    p.add_argument("--exact", action="store_true")
    args = p.parse_args()
    print(json.dumps(report(args.directory, args.directory / "annotations.json", args.exact),
                     ensure_ascii=False, indent=2))
