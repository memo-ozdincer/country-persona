"""Verify fixed and adaptive reply evidence from locked sources and token IDs."""
import argparse
import json
from pathlib import Path

from transformers import AutoTokenizer

from run import CAP, HERE, adaptive, digest, evaluate, fixed_specs, old_rows, paired, serialize


def verify(run):
    launch = json.loads((run / "launch.json").read_text())
    root = HERE.parent.parent.parent
    assert launch["optimizer_updates"] == 0
    for path, expected in launch["sha256"].items():
        assert digest(root / path) == expected
    tok = AutoTokenizer.from_pretrained(launch["model"], local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    rows = old_rows()
    replay = {}

    def stage(name, reconstruct):
        raw = run / f"{name}.jsonl"
        rows = [json.loads(line) for line in raw.read_text().splitlines()]
        receipt = json.loads((run / f"{name}-receipt.json").read_text())
        pending = {row["id"]: row for row in rows}
        assert len(rows) == len(pending) == receipt["records"] == 16
        assert receipt["optimizer_updates"] == 0 and digest(raw) == receipt["sha256"]
        cap_hits = 0
        input_tokens = 0
        output_tokens = 0

        def generate(specs, label):
            nonlocal cap_hits, input_tokens, output_tokens
            assert label == name
            out = {}
            for expected, role, menu, option in specs:
                row = pending.pop(expected["id"])
                assert all(row[k] == value for k, value in expected.items())
                assert row["role"] == role and row["query"] == option
                prompt = tok.apply_chat_template(row["messages"], tokenize=False, add_generation_prompt=True,
                                                 enable_thinking=False)
                assert tok.encode(prompt, add_special_tokens=False) == row["input_ids"]
                tail = row["output_ids"]
                assert 0 < len(tail) <= CAP and eos not in tail[:-1]
                assert tail[-1] == eos or len(tail) == CAP
                assert tok.decode(tail, skip_special_tokens=True).strip() == row["output"]
                assert evaluate(row["output"], row["id"], role, menu, "query", option) == row["judgment"]
                cap_hits += tail[-1] != eos
                input_tokens += len(row["input_ids"])
                output_tokens += len(tail)
                out[row["id"]] = row
            return out

        metrics = reconstruct(generate)
        assert not pending and metrics == json.loads((run / f"{name}-metrics.json").read_text())
        replay[name] = {"records": len(rows), "sha256": receipt["sha256"], "cap_hits": cap_hits,
                        "input_tokens": input_tokens, "output_tokens": output_tokens}
        return metrics

    fixed = stage("fixed", lambda generate: paired(rows, generate(list(fixed_specs(rows)), "fixed")))
    replay["paired_transitions"] = fixed["transitions"]
    if (run / "adaptive-receipt.json").exists():
        live = stage("adaptive", lambda generate: adaptive(rows, generate))
        replay["first_certificates"] = {k: v["first_certificate"] for k, v in live.items()}
    return replay


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    print(serialize(verify(parser.parse_args().run)))
