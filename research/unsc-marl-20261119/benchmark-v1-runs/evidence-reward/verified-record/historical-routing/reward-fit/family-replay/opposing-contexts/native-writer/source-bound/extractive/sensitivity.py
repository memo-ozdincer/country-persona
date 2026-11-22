"""Re-score with a 27-word national excerpt cap as a diagnostic."""
import json
from unittest.mock import patch

import extract_writer as x

b, n, e = x.b, x.n, x.n.matched.e


def replay():
    call = next(row for row in x.score.calls() if row["part"] == "Brazil")
    source = json.loads(call["request"]["messages"][-1]["content"])["source"]
    original = json.loads(call["response"]["text"])["excerpts"]
    assert source == " ".join(original) and sum(len(z.split()) for z in original) == 27
    assert x.admit("Brazil", call["response"], source)["issues"] == ["invalid_excerpts"]
    native = x.score.fragments()
    assert not native["China"]["summary"] and not native["Brazil"]["summary"]
    # Plain admission renders the verified excerpts without relying on the faulty mission tag.
    record = "Brazil position: " + " ".join("“" + line + "”" for line in original)
    native["Brazil"] = {"summary": record, "mission_support_quote": "", "host_concerns": None, "issues": []}
    with patch.object(x.score, "fragments", return_value=native):
        case, packets = x.score.packets()
    marks = n.read(x.HERE / "marks.json")
    scores = {}
    for mask, row in packets.items():
        mark = marks[str(mask)]
        mark["id"] = row["record"]["id"]
        if mask & 1:
            unit = next(r for r in mark["units"] if r["id"] == "brazil-reason")
            unit.update(status="met", response=record, source=[{"block": "brazil", "quote": source}],
                        reason="The exact Brazil excerpt preserves free operation and partial accommodation.")
        scores[mask] = e.final_score(case, row["calls"], mark)
    return {"retained_brazil_excerpt_words": 27, "released": {m: s["released_70"] for m, s in scores.items()},
            "frozen_route_comparison": n.comparison({m: s["released_70"] for m, s in scores.items()})}


if __name__ == "__main__":
    with patch.multiple(b, HERE=x.HERE, OUT=x.OUT, plan=x.plan, admit=x.admit):
        e.emit(replay())
