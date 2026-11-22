"""Check guard outcomes and diagnose malformed coverage without admitting repaired text."""
import json
from pathlib import Path
from hashlib import sha256

HERE = Path(__file__).resolve().parent


def run():
    raw_path = HERE / "evidence/calls.jsonl"
    calls = {r["request"]["id"]: r for r in map(json.loads, raw_path.read_text().splitlines())}
    output = {}
    for case in ("emergency", "myanmar", "unama"):
        for mask in ("pair", "control"):
            key = f"{case}/{mask}"
            support = calls[key + "/support"]
            data = json.loads(support["request"]["messages"][-1]["content"])
            labels = json.loads(support["response"]["text"])
            assert support["response"]["termination"] == "complete"
            assert len(labels) == len(data["candidate_paragraphs"])
            expect = ["Y"] * len(labels)
            if key == "emergency/control":
                expect[-1] = "N"
            output[key] = {"expected_labels": expect, "model_labels": labels,
                           "record_guard_agrees": ("N" in expect) == ("N" in labels) and "U" not in labels}
    candidate_path = calls["myanmar/pair/coverage"]
    raw = candidate_path["response"]["text"]
    wrapped = json.loads("[" + raw + "]")
    assert len(wrapped) == 10 and all(isinstance(group, list) for group in wrapped)
    references = [n for sublist in wrapped[4] for n in sublist]
    # Fifth criterion is the scoped chair-procedure clause in the archived prompt.
    payload = json.loads(candidate_path["request"]["messages"][-1]["content"])
    assert "President" in payload["criteria_in_order"][4]
    paragraphs = dict(payload["candidate_paragraphs"])
    assert all("presiden" not in paragraphs[i].lower() for i in references)
    return {"support": output,
            "paragraph_verdicts_matched": sum(sum(x == y for x, y in zip(r["expected_labels"], r["model_labels"], strict=True))
                                              for r in output.values()),
            "paragraph_verdicts_total": sum(len(r["expected_labels"]) for r in output.values()),
            "record_guards_matched": sum(r["record_guard_agrees"] for r in output.values()),
            "myanmar_wrap_only_diagnostic": {"purpose": "Inspect semantic error beyond malformed formatting.",
                                             "criterion": payload["criteria_in_order"][4],
                                             "cited_record_ids": references, "admitted": False},
            "input_sha256": sha256(raw_path.read_bytes()).hexdigest()}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
