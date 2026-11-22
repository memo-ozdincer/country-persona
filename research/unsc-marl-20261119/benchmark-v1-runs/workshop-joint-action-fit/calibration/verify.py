"""Rebuild paired prompts and replay the two dependent CPU fits."""
import json
import numpy as np
from transformers import AutoTokenizer

import encode_conflict as encoding
import fit_conflict as conflict
import fit_balanced as balanced

HERE, E, fit = conflict.HERE, conflict.E, conflict.fit


def run():
    cases = encoding.conflict_roster.run()
    assert cases == E.read(HERE / "conflict-roster.json")
    expected = {}
    for split, rows in cases.items():
        for positive, negative in zip(rows[::2], rows[1::2], strict=True):
            assert positive["kind"] == "consistent" and negative["kind"] == "contradictory"
            assert negative["supported"] == ["U"] and "U" not in positive["supported"]
            assert positive["messages"][0] == negative["messages"][0]
            a, b = (json.loads(row["messages"][1]["content"]) for row in (positive, negative))
            assert a["menu"] == b["menu"] and a["public_notes"][0] == b["public_notes"][0]
            first, second = a["public_notes"][1], b["public_notes"][1]
            assert first[:-2] == second[:-2] and first[-2] != second[-2]
            for row in (positive, negative):
                expected[f'{split}/{row["id"]}'] = row["messages"]
    d = conflict.EVIDENCE
    t = AutoTokenizer.from_pretrained(encoding.encode.MODEL, local_files_only=True)
    action_ids = [t.encode(token, add_special_tokens=False)[0] for token in fit.env.DECISIONS]
    vectors = np.load(d / "features.npz")
    traces = [json.loads(line) for line in (d / "trace.jsonl").read_text().splitlines()]
    assert len(traces) == len(expected) == 48
    assert {r["id"] for r in traces} == expected.keys()
    for trace in traces:
        text = t.apply_chat_template(expected[trace["id"]], tokenize=False,
                                     add_generation_prompt=True, enable_thinking=False)
        assert trace["input_ids"] == t.encode(text, add_special_tokens=False)
        assert trace["action_ids"] == action_ids
        assert np.isfinite(vectors[trace["id"] + "/hidden"]).all()
        np.testing.assert_array_equal(vectors[trace["id"] + "/logits"],
                                      np.asarray(trace["restricted_logits"], dtype=np.float32))
    assert balanced.run() == E.read(HERE / "balanced.json")
    assert conflict.run() == E.read(HERE / "conflict.json")
    return {"verified_prompts": len(traces), "synthetic_train_conflict_pairs": 16,
            "held_un_conflict_pairs": 8, "paired_by_single_endorsed_option": True, "exact_cpu_replays": 2}


if __name__ == "__main__":
    E.emit(run())
