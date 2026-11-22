"""Score both arms with the previous judge and track the actual call costs."""

import json
from unittest.mock import patch

from study_driver import HERE, LOCAL, PRIOR, VIEWS, previous, read

scorer = previous.load("quoted_purpose_scorer", PRIOR / "score.py")
reason_before = HERE.parent / "reason-before-vote"


def run():
    archive = read(HERE / "verified.json")
    evaluations = read(HERE / "marks.json")
    assert evaluations.keys() == archive["chair"].keys()
    partial = {k for k in previous.ORDERS if k not in VIEWS}
    partial_verified = read(reason_before / "verified.json")["outputs"]
    partial_marks = read(reason_before / "marks.json")
    assert all(partial_verified[k]["text"] == "NONE" for k in partial)
    case_scores = {}
    for arm in ("direct", "quotes"):
        outputs = {key: partial_verified[key] for key in partial}
        outputs.update({key: archive["chair"][f"{arm}/{key}"] for key in VIEWS})
        marks = {key: partial_marks[key] for key in partial}
        marks.update({key: evaluations[f"{arm}/{key}"] for key in VIEWS})
        virtual = {"verified.json": {"outputs": outputs}, "marks.json": marks}
        old_read = previous.base.read
        with patch.object(scorer, "HERE", HERE), patch.object(
            previous.base, "read", side_effect=lambda p: virtual[p.name] if p.parent == HERE and p.name in virtual
            else old_read(p)
        ):
            case_scores[arm] = scorer.score()
    output = {}
    for key, cards in VIEWS.items():
        rows = {}
        for arm, grade in case_scores.items():
            answer = archive["chair"][f"{arm}/{key}"]
            score = grade["outcomes"][key]
            call_cost = [answer]
            if arm == "quotes":
                call_cost.extend(archive["extractions"][card]["reply"] for card in cards)
            rows[arm] = score | {
                "chair_input_tokens": answer["input_tokens"],
                "logical_input_tokens": sum(r["input_tokens"] for r in call_cost),
                "logical_output_tokens": sum(r["output_tokens"] for r in call_cost),
            }
        output[key] = rows | {"quotes_minus_direct": rows["quotes"]["known_pair"] - rows["direct"]["known_pair"]}
    both_quotes = {}
    for key, cards in VIEWS.items():
        comparison = output[key]["quotes"]
        admitted = all(archive["extractions"][card]["admitted"] for card in cards)
        both_quotes[key] = {
            "would_call": admitted,
            "released_70": comparison["always_call"] if admitted else comparison["standalone"],
        }
    return {
        "evaluated_pairs": output,
        "require_two_admitted_quotes": both_quotes,
        "admitted_quotes": {key: archive["extractions"][key]["admitted"] for key in LOCAL},
        "partial_scores_from_matched_prior_abstentions": {
            key: case_scores["direct"]["outcomes"][key]["standalone"] for key in sorted(partial)
        },
    }


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
