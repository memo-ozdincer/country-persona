"""Replay the locked relation prompts while retaining native reviewer features."""
import argparse
import json
from pathlib import Path
import sys
from unittest.mock import patch

import numpy as np

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
OUT = HERE / "evidence"
sys.path.insert(0, str(PARENT))
import balance as lab

held, e, team, base = lab.held, lab.e, lab.team, lab.held.base
SEED, FEATURES = 2669, 32


def asks():
    for row in lab.identity():
        yield {k: row[k] for k in ("observation", "legal", "messages")} | {"max_output_tokens": 2}
    yield from lab.requests()


def plan():
    files = (Path(__file__), HERE / "protocol.md", PARENT / "plan.json", PARENT / "verified.json",
             PARENT / "results.json", PARENT / "credit-audit.json", Path(base.__file__), Path(held.__file__))
    rows = list(asks())
    assert len(rows) == len({tuple(r["observation"]) for r in rows}) == 81
    return {"requests": rows, "projection": {"seed": SEED, "dimensions": FEATURES},
            "sha256": {str(f.relative_to(team.STUDY)): team.pin(f) for f in files}}


def lock():
    assert plan() == team.read(HERE / "plan.json")


def append(path, row):
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, ensure_ascii=False) + "\n")


def run():
    import torch
    from transformers import AutoTokenizer
    from transformers.generation.utils import GenerationMixin

    lock()
    tok = AutoTokenizer.from_pretrained(base.MODEL, local_files_only=True)
    ids, eos = held.ids(tok), tok.convert_tokens_to_ids("<|im_end|>")
    state = {}

    def native(model, *args, **kwargs):
        prefix = kwargs["input_ids"]
        assert prefix[0].tolist() == base.prompt(tok, state["request"])
        result = model(input_ids=prefix, attention_mask=kwargs["attention_mask"], use_cache=False,
                       logits_to_keep=1, output_hidden_states=True)
        vector = result.hidden_states[-1][0, -1].float().cpu().numpy()
        if "matrix" not in state:
            state["matrix"] = np.random.default_rng(SEED).standard_normal((vector.size, FEATURES))
        compact = (vector / np.linalg.norm(vector)) @ state["matrix"]
        scores = result.logits[0, -1].float()[ids].tolist()
        state["scores"], state["hidden"] = scores, compact.tolist()
        pick = max(range(len(scores)), key=scores.__getitem__)
        suffix = torch.tensor([[ids[pick], eos]], dtype=prefix.dtype, device=prefix.device)
        return torch.cat((prefix, suffix), dim=-1)

    def collect(generate, directory):
        for row in asks():
            state["request"] = row
            response = generate(row)
            append(directory / "calls.jsonl", row | {"reply": response, "scores": state.pop("scores"),
                                                      "features": state.pop("hidden")})

    with patch.object(GenerationMixin, "generate", native), patch.object(held.suite, "collect", collect), patch.object(
            base, "HERE", HERE), patch.object(base, "roster", return_value={"semantic-credit": {}}):
        base.run(OUT)


def lines(name):
    return [json.loads(x) for x in (OUT / name).read_text().splitlines()]


def verify():
    from transformers import AutoTokenizer

    lock()
    manifest = team.read(OUT / "complete.json")
    assert set(manifest) == {"calls.jsonl", "tokens.jsonl", "launch.json"}
    assert all(team.pin(OUT / f) == digest for f, digest in manifest.items())
    launch = team.read(OUT / "launch.json")
    assert launch["cases"] == ["semantic-credit"] and launch["optimizer_updates"] == 0
    assert launch["checkpoint_index_sha256"] == held.report.plan()["checkpoint_index_sha256"]
    assert launch["collector_sha256"] == team.pin(Path(base.__file__))
    assert launch["release_sha256"] == team.pin(held.report.RELEASE / "release.json")
    assert launch["protocol_sha256"] == team.pin(HERE / "protocol.md")
    tok = AutoTokenizer.from_pretrained(base.MODEL, local_files_only=True)
    ids, eos = held.ids(tok), tok.convert_tokens_to_ids("<|im_end|>")
    calls, tokens = lines("calls.jsonl"), lines("tokens.jsonl")
    for row, request, trace in zip(calls, asks(), tokens, strict=True):
        assert all(row[k] == v for k, v in request.items())
        assert trace["input_ids"] == base.prompt(tok, request)
        assert row["reply"] == trace["response"] and len(trace["input_ids"]) == row["reply"]["input_tokens"]
        scores = row["scores"]
        assert len(scores) == 3 and np.isfinite(scores).all()
        assert len(row["features"]) == FEATURES and np.isfinite(row["features"]).all()
        selected = max(range(3), key=scores.__getitem__)
        assert trace["output_ids"] == [ids[selected], eos] and row["reply"]["text"] == "ABC"[selected]
    assert len(calls) == 81
    return {"records": len(calls), "evidence_sha256": manifest, "dimensions": FEATURES,
            "input_tokens": sum(r["reply"]["input_tokens"] for r in calls),
            "output_tokens": sum(r["reply"]["output_tokens"] for r in calls)}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("plan", "run", "verify"))
    mode = p.parse_args().mode
    if mode == "run":
        run()
    else:
        e.emit({"plan": plan, "verify": verify}[mode]())
