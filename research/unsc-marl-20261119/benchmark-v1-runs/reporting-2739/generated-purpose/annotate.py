"""Review generated-purpose records against the original 2739 criterion."""
import json

from assess import scorer
from purpose_study import HERE, VIEWS, read


def marks():
    output = {}
    answers = read(HERE / "verified.json")["cases"]
    for name, ids in VIEWS.items():
        row = answers[name]
        assert row["generated"]["text"] == "to keep the Council informed"
        assert row["candidate"]
        evidence = scorer.citations(*ids)
        overlap = row["exact_quote_pair"]
        explanation = (
            "The rendered sentence explicitly identifies the Council-information purpose supported by both "
            "statements and keeps Algeria's abstention distinct."
            if overlap else
            "The public adopted action and Algeria's position do not establish the co-sponsors' stated purpose."
        )
        output[name] = {
            "overlap": {"id": "bounded-overlap", "status": "met" if overlap else "unmet",
                        "source": evidence, "response": row["candidate"], "reason": explanation},
            "guard": {"status": "clear" if overlap else "failed", "source": [] if overlap else evidence,
                      "response": "" if overlap else row["candidate"], "reason": explanation},
        }
    return output


if __name__ == "__main__":
    print(json.dumps(marks(), ensure_ascii=False, indent=2))
