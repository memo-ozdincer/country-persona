"""Verify stored Qwen judge prompts, tokens and scores without loading weights."""
import hashlib
import json
from pathlib import Path
import sys

from transformers import AutoTokenizer

HERE = Path(__file__).resolve().parent
JUDGE = HERE.parent
sys.path.insert(0, str(JUDGE))
from score import request, score


def main():
    launch = json.loads((HERE / "launch.json").read_text())
    for path in (HERE / "run.py", JUDGE / "instructions.md", JUDGE / "calibration.json", JUDGE / "score.py"):
        assert hashlib.sha256(path.read_bytes()).hexdigest() == launch["inputs_sha256"][path.name]
    raw = HERE / "responses.json"
    responses = json.loads(raw.read_text())
    fixtures = {r["request"]["id"]: r for r in json.loads((JUDGE / "calibration.json").read_text())["final_calibration"]}
    tok = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    results = []
    assert {r["id"] for r in responses} == {"T17-7", "T17-2"} and len(responses) == 2
    for r in responses:
        fixture = fixtures[r["id"]]
        assert r["messages"][0]["content"] == (JUDGE / "instructions.md").read_text()
        assert json.loads(r["messages"][1]["content"]) == request(fixture["request"])
        prompt = tok.apply_chat_template(r["messages"], tokenize=False, add_generation_prompt=True, enable_thinking=False)
        assert tok.encode(prompt, add_special_tokens=False) == r["input_ids"]
        assert tok.decode(r["output_ids"], skip_special_tokens=True).strip() == r["raw_response"]
        assert 0 < len(r["output_ids"]) <= 768
        assert r["output_ids"][-1] == eos and r["stop"] == "eos"
        verdict = json.loads(r["raw_response"])
        observed = score(fixture["request"], verdict)
        assert r["score"] == observed
        expected_units = {u["id"]: u["status"] for u in fixture["authored_verdict"]["units"]}
        actual_units = {u["id"]: u["status"] for u in verdict["units"]}
        disagree = sorted(k for k, v in expected_units.items() if actual_units[k] != v)
        assert r["unit_agreement"] == len(expected_units) - len(disagree)
        assert r["guard_agreement"] == (observed["guard"] == fixture["score"]["guard"])
        results.append({
            "id": r["id"], "validated": True, "input_tokens": len(r["input_ids"]),
            "output_tokens": len(r["output_ids"]), "calibration_score": fixture["score"]["final"],
            "judge_score": observed["final"], "unit_agreement": r["unit_agreement"],
            "disagreed_units": disagree, "guard_agreement": r["guard_agreement"], "guard": observed["guard"],
        })
    print(json.dumps({"response_sha256": hashlib.sha256(raw.read_bytes()).hexdigest(),
                      "optimizer_updates": launch["optimizer_updates"], "results": results}, indent=2))


if __name__ == "__main__":
    main()
