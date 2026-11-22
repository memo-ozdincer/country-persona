"""Replay the tokenizer inputs, masks, captured vectors, and policy fit."""
from pathlib import Path
import json

import numpy as np
from transformers import AutoTokenizer

import encode
import environment as env
import fit


def verify():
    directory = env.HERE / "evidence"
    rows = env.roster()
    assert rows == env.E.read(env.HERE / "roster.json")
    expected = {}
    for split, cases in rows.items():
        for case in cases:
            prefix = f'{split}/{case["id"]}'
            if split == "archived":
                expected[prefix + "/archived"] = (case["chair"], env.DECISIONS)
            else:
                expected[prefix + "/responder"] = (case["responder"], env.RESPONSES)
                for act, prompt in zip(env.RESPONSES, case["chair"], strict=True):
                    expected[prefix + "/" + act] = (prompt, env.DECISIONS)
    tokenizer = AutoTokenizer.from_pretrained(encode.MODEL, local_files_only=True)
    features = np.load(directory / "features.npz")
    seen = set()
    for row in map(json.loads, (directory / "trace.jsonl").read_text().splitlines()):
        key = row["id"]
        assert key not in seen
        seen.add(key)
        prompt, letters = expected[key]
        text = tokenizer.apply_chat_template(prompt, add_generation_prompt=True, tokenize=False, enable_thinking=False)
        assert tokenizer.encode(text, add_special_tokens=False) == row["input_ids"]
        assert row["action_ids"] == {k: tokenizer.encode(k, add_special_tokens=False)[0] for k in letters}
        for field in ("hidden", "logits"):
            vector = features[key + "/" + field]
            assert vector.ndim == 1 and np.isfinite(vector).all()
        np.testing.assert_array_equal(features[key + "/logits"], np.asarray(row["restricted_logits"], dtype=np.float32))
    assert seen == expected.keys() and len(features.files) == len(seen) * 2
    assert fit.run() == env.E.read(Path(__file__).with_name("results.json"))
    return {"verified_prompts": len(seen), "training_worlds": len(rows["train"]),
            "held_native_prompt_worlds": len(rows["held"]), "archived_note_pairs": len(rows["archived"]),
            "exact_cpu_fit_replay": True}


if __name__ == "__main__":
    env.E.emit(verify())
