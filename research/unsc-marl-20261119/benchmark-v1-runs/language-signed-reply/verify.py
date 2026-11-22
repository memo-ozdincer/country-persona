"""Verify branch labels, captured native-token inputs and the CPU replay."""
import json

import numpy as np
from transformers import AutoTokenizer

import fit
import capture
import cases


def run():
    root = cases.HERE
    assert fit.HERE == root
    evidence = root / "evidence"
    receipt = cases.E.read(evidence / "launch.json")
    assert receipt["sha256"] == {p.name: capture.digest(p) for p in (
        root / "capture.py", root / "cases.py", root / "protocol.md", root / "roster.json", cases.E.HERE / "release.json")}
    roster = cases.roster()
    assert roster == cases.E.read(root / "roster.json")
    tokenizer = AutoTokenizer.from_pretrained(capture.MODEL, local_files_only=True)
    action_ids = [tokenizer.encode(t, add_special_tokens=False)[0] for t in cases.DEC]
    traces = [json.loads(line) for line in (evidence / "trace.jsonl").read_text().splitlines()]
    features = np.load(evidence / "vectors.npz")
    expected = [(f'{split}/{row["id"]}', row["messages"]) for split, rows in roster.items() for row in rows]
    assert len(expected) == len(traces) == len(features["hidden"]) == len(features["logits"])
    assert np.isfinite(features["hidden"]).all()
    for i, ((identifier, messages), row) in enumerate(zip(expected, traces, strict=True)):
        assert row["id"] == identifier and row["action_ids"] == action_ids
        assert row["input_ids"] == capture.encode(tokenizer, messages)
        np.testing.assert_array_equal(features["logits"][i], np.asarray(row["restricted_logits"], dtype=np.float32))
    assert fit.run() == cases.E.read(root / "results.json")
    return {"verified_prompts": len(traces), "development": len(roster["train"]), "held": len(roster["held"]),
            "action_token_ids": action_ids, "exact_fit_replays": 2}


if __name__ == "__main__":
    cases.E.emit(run())
