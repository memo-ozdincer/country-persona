"""One GPU collection for generated shared-purpose phrases and semantic verification."""
import argparse
import json
from math import isfinite
import os
from pathlib import Path
import re
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
QUOTES = HERE.parent / "quoted-purpose"
REGISTRY = HERE.parents[1] / "relation-support-transfer"
OUT = HERE / "evidence"
sys.path.insert(0, str(QUOTES))
import study_driver as earlier

collector = earlier.collector
previous = earlier.previous
VIEWS = earlier.VIEWS
GENERATOR = (
    "Read the two delivered cards. Identify the shared practical purpose that each delegation "
    "explicitly gives for continued reporting, even if they describe it in different words. "
    "Return only a short infinitive beginning with 'to', at most 14 words. No punctuation or labels. "
    "If either card supplies no delegation's stated purpose, or the purposes do not overlap, "
    "return exactly NONE. Output only that phrase or NONE."
)


def read(path):
    return json.loads(path.read_text())


def plan():
    inputs = (Path(__file__), HERE / "protocol.md", QUOTES / "study_driver.py", QUOTES / "plan.json",
              QUOTES / "verified.json", QUOTES / "scores.json", REGISTRY / "plan.json",
              HERE.parent / "docket.json", previous.base.RELEASE / "release.json", Path(collector.__file__))
    quoted = read(QUOTES / "verified.json")["extractions"]
    evidence = {}
    for key in earlier.LOCAL:
        span = quoted[key]["admitted"]
        assert span == earlier.admit(quoted[key]["reply"], previous.CARDS[key])
        evidence[key] = {"id": key, "text": previous.CARDS[key]}
        if span:
            evidence[key]["purpose_quote"] = span
    source_gate = read(REGISTRY / "plan.json")
    gate_rows = [r for r in source_gate["requests"] if r["id"].startswith("reporting-canonical/")]
    templates = {r["id"].split("/")[-1]: json.loads(r["messages"][1]["content"])["responses"] for r in gate_rows}
    assert set(templates) == {"ab", "ba"} and len({r["messages"][0]["content"] for r in gate_rows}) == 1
    assert all(r["max_output_tokens"] == 2 for r in gate_rows)
    return {
        "pins": {str(p.relative_to(previous.RUNS.parent)): collector.sha(p) for p in inputs},
        "checkpoint_index_sha256": source_gate["checkpoint_index_sha256"],
        "cases_in_order": list(VIEWS), "generator": GENERATOR, "generator_cap": 45,
        "verifier": gate_rows[0]["messages"][0]["content"], "verifier_labels": templates,
        "evidence": evidence,
        "frame": "The co-sponsors and Algeria shared a reason for continued reporting: {purpose}, although Algeria abstained on the resolution.",
    }


def locked():
    spec = plan()
    assert spec == read(HERE / "plan.json")
    return spec


def candidate(reply, config):
    text = reply["text"]
    if reply["termination"] != "complete" or len(text.split()) > 14:
        return ""
    if not re.fullmatch(r"to [\w]+(?:[ ’'-][\w]+)*", text, flags=re.IGNORECASE):
        return ""
    return config["frame"].format(purpose=text)


def episode(call, config):
    cases = {}
    for view, ids in VIEWS.items():
        cards = [config["evidence"][key] for key in ids]
        reply = call(earlier.request(f"{view}/generate", config["generator_cap"], config["generator"], {
            "delivered": cards,
        }))
        sentence = candidate(reply, config)
        verdicts = {}
        if sentence:
            source_cards = [{k: card[k] for k in ("id", "text")} for card in cards]
            for label_order, labels in config["verifier_labels"].items():
                verdicts[label_order] = call(earlier.request(f"{view}/{label_order}", 2, config["verifier"], {
                    "delivered": source_cards, "candidate_comparison": sentence, "responses": labels,
                }))
        cases[view] = {"cards": ids, "generated": reply, "candidate": sentence, "verifier": verdicts,
                       "exact_quote_pair": set(ids) == {"sponsors", "algeria"} and all(c.get("purpose_quote") for c in cards)}
    return cases


def run():
    import torch
    from transformers import AutoTokenizer
    from transformers.generation.utils import GenerationMixin

    config = locked()
    assert os.environ.get("CUDA_VISIBLE_DEVICES", "").startswith("GPU-")
    tokenizer = AutoTokenizer.from_pretrained(collector.MODEL, local_files_only=True)
    ids = label_tokens(tokenizer)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    original = GenerationMixin.generate
    state = {}

    def generate(model, *args, **kwargs):
        if state["request"]["max_output_tokens"] != 2:
            return original(model, *args, **kwargs)
        vector = kwargs["input_ids"]
        assert vector[0].tolist() == collector.prompt(tokenizer, state["request"])
        values = model(input_ids=vector, attention_mask=kwargs["attention_mask"],
                       use_cache=False, logits_to_keep=1).logits[0, -1].float()
        logits = {key: values[token].item() for key, token in ids.items()}
        assert all(isfinite(v) for v in logits.values())
        state["logits"] = logits
        result = torch.tensor([[ids[max(logits, key=logits.get)], eos]], device=vector.device, dtype=vector.dtype)
        return torch.cat((vector, result), dim=-1)

    def collect(generate_response, directory):
        def call(spec):
            state["request"] = spec
            answer = generate_response(spec)
            row = {"request": spec, "reply": answer, "logits": state.pop("logits", {})}
            collector.suite.append(directory / "calls.jsonl", row)
            return answer | {"logits": row["logits"]}
        (directory / "candidates.json").write_text(json.dumps(episode(call, config), ensure_ascii=False, indent=2) + "\n")

    with patch.object(GenerationMixin, "generate", generate), patch.object(
        collector.suite, "collect", collect
    ), patch.object(collector, "roster", return_value={"reporting-2739-generated-purpose": previous.CASE}), patch.object(
        collector, "HERE", HERE
    ), patch.object(collector.suite.e, "HERE", previous.base.RELEASE):
        collector.run(OUT)


def label_tokens(tokenizer):
    ids = {letter: tokenizer.encode(letter, add_special_tokens=False) for letter in ("A", "B")}
    assert all(len(v) == 1 for v in ids.values()) and ids["A"] != ids["B"]
    return {letter: value[0] for letter, value in ids.items()}


def verify():
    from transformers import AutoTokenizer

    config = locked()
    manifest = read(OUT / "complete.json")
    assert set(manifest) == {"calls.jsonl", "launch.json", "tokens.jsonl", "candidates.json"}
    assert all(collector.sha(OUT / name) == digest for name, digest in manifest.items())
    launch = read(OUT / "launch.json")
    assert launch["optimizer_updates"] == 0 and launch["checkpoint_index_sha256"] == config["checkpoint_index_sha256"]
    assert launch["gpu_name"] == "NVIDIA RTX PRO 6000 Blackwell Server Edition"
    tokenizer = AutoTokenizer.from_pretrained(collector.MODEL, local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    ids = label_tokens(tokenizer)
    calls, tokens = ([json.loads(line) for line in (OUT / name).read_text().splitlines()]
                     for name in ("calls.jsonl", "tokens.jsonl"))
    saved = iter(zip(calls, tokens, strict=True))

    def call(spec):
        row, trace = next(saved)
        response = row["reply"]
        assert row["request"] == spec and trace["response"] == response
        assert trace["input_ids"] == collector.prompt(tokenizer, spec)
        assert len(trace["input_ids"]) == response["input_tokens"]
        output = trace["output_ids"]
        assert 0 < len(output) == response["output_tokens"] <= spec["max_output_tokens"]
        assert tokenizer.decode(output, skip_special_tokens=True).strip() == response["text"]
        assert eos not in output[:-1] and (output[-1] == eos) == (response["termination"] == "complete")
        logits = row["logits"]
        if spec["max_output_tokens"] == 2:
            assert set(logits) == set(ids) and all(isfinite(v) for v in logits.values())
            assert output == [ids[max(logits, key=logits.get)], eos]
        else:
            assert not logits
        return response | {"logits": logits}

    cases = episode(call, config)
    assert next(saved, None) is None
    assert read(OUT / "candidates.json") == json.loads(json.dumps(cases))
    return {"manifest": manifest, "calls": len(calls), "cases": cases}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    if mode == "run":
        run()
    else:
        print(json.dumps((plan if mode == "plan" else verify)(), ensure_ascii=False, indent=2))
