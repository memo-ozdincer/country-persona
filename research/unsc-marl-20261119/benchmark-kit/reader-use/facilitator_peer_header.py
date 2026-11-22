"""Test a narrow postprocessor for decisive, source-local labels."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "facilitator-peer-findings-evidence"
REPAIR = HERE / "facilitator-peer-quote-repair-evidence"


def transcript(path):
    return {r["id"]: r for r in map(json.loads, path.read_text().splitlines())}


def header_rule(text, decisive):
    if decisive == "withhold":
        return text
    _, separator, body = text.partition("|")
    if separator:
        return f"{decisive} |{body}"
    return text


def evaluate():
    artifact = REPAIR / "results.json"
    prior = json.loads(artifact.read_text())
    assert prior["repaired_final_only"]
    rows = transcript(BASE / "transcript.jsonl") | transcript(REPAIR / "transcript.jsonl")
    counts, details = {}, {}
    for name, item in prior["episodes"].items():
        score = item["grade"]
        assert score["criteria"]["format"] == 10
        response = rows[item["steps"][-1]]["output"]
        proposal = header_rule(response, item["mechanical_disposition"])
        action, sep, _ = proposal.partition("|")
        disposition = action.strip().casefold() if sep else None
        right = disposition == score["expected"]
        value = sum(score["criteria"].values()) - score["criteria"]["disposition"] + 14 * right
        admitted = item["local"].values()
        if disposition == "retain":
            basis = all(r["admitted"]["relation"] == "supports" and r["witness"] == "adequate" for r in admitted)
        elif disposition == "revise":
            basis = any(r["admitted"]["relation"] == "contradicts" and r["witness"] == "adequate" for r in admitted)
        else:
            basis = False
        changed = disposition != score["disposition"]
        assert proposal.partition("|")[2] == response.partition("|")[2]
        score_strict = value == 70
        summary = counts.setdefault(name.rsplit("/", 1)[1], Counter())
        summary.update({"panels": 1, "points": value, "correct": right, "strict": score_strict,
                        "changed": changed, "inadequate_witness_changes": changed and not basis,
                        "strict_with_adjudicated_basis": score_strict and (not changed or basis)})
        details[name] = {"response": proposal, "strict": score_strict, "points": value, "disposition": disposition,
                         "changed": changed, "adequate_basis": basis, "expected": score["expected"]}
    return {"scope": "Post hoc heading-only experiment. Deterministic label composition preserves the body. "
                     "Witness adequacy from the manual review is reported separately from the runtime rule.",
            "summary": counts, "records": details,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in (Path(__file__), artifact)}}


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2, ensure_ascii=False))
