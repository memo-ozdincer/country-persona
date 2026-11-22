"""Score candidate construction, semantic verification, and gated release separately."""
import json
from unittest.mock import patch

from purpose_study import HERE, QUOTES, VIEWS, locked, previous, read

PRIOR = HERE.parent / "source-preserving-transfer"
scorer = previous.load("generated_purpose_scorer", PRIOR / "score.py")


def mean_margin(answers, mappings):
    if not answers:
        return None
    assert answers.keys() == mappings.keys()
    margins = []
    for key, mapping in mappings.items():
        support = next(label for label, value in mapping.items() if value == "supported")
        reject = next(label for label, value in mapping.items() if value == "unsupported")
        scores = answers[key]["logits"]
        margins.append(scores[support] - scores[reject])
    return sum(margins) / len(margins)


def run():
    configuration = locked()
    evidence = read(HERE / "verified.json")
    cases = evidence["cases"]
    base_archive = read(PRIOR / "verified.json")["outputs"]
    grades = read(PRIOR / "marks.json")
    quotes = read(QUOTES / "scores.json")["evaluated_pairs"]
    observed = read(HERE / "marks.json")
    assert cases.keys() == observed.keys() == VIEWS.keys()
    for name, case in cases.items():
        assert case["candidate"] or not case["verifier"]
        base_archive[name] = case["generated"] | {"text": case["candidate"] or "NONE"}
        grades[name] = observed[name]
    virtual = {"verified.json": {"outputs": base_archive}, "marks.json": grades}
    old_read = previous.base.read
    with patch.object(scorer, "HERE", HERE), patch.object(
        previous.base, "read",
        side_effect=lambda path: virtual[path.name] if path.parent == HERE and path.name in virtual else old_read(path)
    ):
        result = scorer.score()
    deployment = {}
    for key, case in cases.items():
        score = result["outcomes"][key]
        margin = mean_margin(case["verifier"], configuration["verifier_labels"])
        admitted = bool(case["exact_quote_pair"] and margin is not None and margin > 0)
        safe = score["standalone"]
        candidate_score = score["always_call"]
        generator = case["generated"]
        verification = list(case["verifier"].values())
        saved_quotes = [read(QUOTES / "verified.json")["extractions"][id_]["reply"] for id_ in case["cards"]]
        deployment[key] = {
            "generated_phrase": generator["text"], "candidate": case["candidate"], "mean_support_margin": margin,
            "exact_quote_pair": case["exact_quote_pair"], "admitted": admitted,
            "standalone": safe, "quote_writer_release": quotes[key]["quotes"]["always_call"],
            "unrestricted_candidate_release": candidate_score,
            "mechanical_only_release": candidate_score if case["exact_quote_pair"] else safe,
            "mechanical_plus_verifier_release": candidate_score if admitted else safe,
            "blockers_if_used": score["blockers"], "full_record_with_candidate": score["record"],
            "new_calls": 1 + len(verification),
            "new_input_tokens": sum(row["input_tokens"] for row in (generator, *verification)),
            "reused_extraction_input_tokens": sum(row["input_tokens"] for row in saved_quotes),
        }
    return {"cases": deployment, "total_new_calls": evidence["calls"]}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
