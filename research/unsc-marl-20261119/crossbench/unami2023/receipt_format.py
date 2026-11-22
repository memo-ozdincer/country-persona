"""Normalize source citation layout without changing record text."""
import json

import receipt_score as study


def normalize(text, required):
    last = 0
    groups = {}
    previous = None
    for match in study.CITATION.finditer(text):
        source = match.group(1)
        content = " ".join(text[last:match.start()].split())
        if source not in required or not content or (source in groups and previous != source):
            return None
        groups.setdefault(source, []).append(content)
        previous = source
        last = match.end()
    if text[last:].strip() or set(groups) != set(required):
        return None
    output = "\n".join(f"{' '.join(pieces)} [{source}]" for source, pieces in groups.items())
    assert study.CITATION.sub("", output).split() == study.CITATION.sub("", text).split()
    return output


def run():
    primary = study.transfer.read(study.EVIDENCE / "results.json")
    public = study.transfer.named_sources()[0]["unami"][3]
    records = {}
    for label, row in primary["bank"].items():
        text = normalize(row["supplement"], row["received"])
        accepted = (text is not None and len(text.split()) <= 106
                    and len(f"{public} {text}".split()) <= 175 and row["guard_clear"])
        assert text is not None
        assert normalize(text, row["received"]) == text
        records[label] = {"supplement": text, "original_form_clear": row["form_clear"], "accepted": accepted,
                          "points": row["record_points"], "meaning_review_applies": row["guard_clear"]}
    assert normalize("A [REVIEW] extra claim", ["REVIEW"]) is None
    assert normalize("A [REVIEW] B [VOTE]", ["REVIEW"]) is None
    assert normalize("A [REVIEW]", ["REVIEW", "SCOPE"]) is None
    assert normalize("A [REVIEW] B [SCOPE] C [REVIEW]", ["REVIEW", "SCOPE"]) is None
    assert normalize("[REVIEW] A", ["REVIEW"]) is None
    routes = {}
    for name, row in primary["routes"].items():
        mass = points = 0.
        for case in row["cases"]:
            for label, probability in case["record_distribution"].items():
                record = records[label]
                mass += probability * record["accepted"]
                points += probability * record["accepted"] * record["points"]
        n = len(row["cases"])
        routes[name] = {"release_probability": mass / n, "release_points": points / n}
    return {"scope": "Posthoc formatting of the same completed supplements. "
                     "Words outside bracketed citation IDs are unchanged and in original order. "
                     "The original semantic review still applies. These rules are restricted to trailing citations.",
            "records": records, "routes": routes, "format_rejection_controls": 5}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
