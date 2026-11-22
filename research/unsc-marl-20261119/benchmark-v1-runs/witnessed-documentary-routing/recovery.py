"""Check whether typographic differences can be mapped back to one exact source span."""
import json

from collect_witnesses import HERE, locked, read

APOSTROPHES = str.maketrans({"’": "'", "‘": "'"})


def recovered_span(response, source):
    raw = response["text"]
    if raw == "NONE" or response["termination"] != "complete":
        return ""
    if raw.startswith('"') and raw.endswith('"'):
        raw = raw[1:-1]
    raw = raw.removesuffix("...").removesuffix("…").strip()
    if not 0 < len(raw.split()) <= 75:
        return ""
    target = raw.translate(APOSTROPHES)
    folded = source.translate(APOSTROPHES)
    start = folded.find(target)
    if start < 0 or folded.find(target, start + 1) >= 0:
        return ""
    return source[start:start + len(target)]


def run():
    spec = locked()
    outputs = read(HERE / "verified.json")["cases"]
    score = read(HERE / "results.json")
    rows = {}
    for key, row in outputs.items():
        span = recovered_span(row["extraction"], spec["views"][key]["text"])
        if span and not row["exact_span"]:
            rows[key] = {"recovered": span, "gate": True, "claim_supported_by_view": score["cases"][key]["target"]}
    return {"recovered_replies": rows, "recovered_true": sum(r["claim_supported_by_view"] for r in rows.values()),
            "recovered_false": sum(not r["claim_supported_by_view"] for r in rows.values())}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
