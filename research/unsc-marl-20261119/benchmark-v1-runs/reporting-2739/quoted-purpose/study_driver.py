"""Collect and replay the quote-conditioned and direct chair passes."""
import argparse
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "source-preserving-transfer"
OUT = HERE / "evidence"
sys.path.insert(0, str(PRIOR))
import study as previous

collector = previous.base.collector
RELEASE = previous.base.RELEASE
VIEWS = {name: cards for name, cards in previous.ORDERS.items() if len(cards) == 2}
LOCAL = ("sponsors", "algeria", "action")
EXTRACT = (
    "Find the reason a delegation gives for valuing or wanting continued reporting. Return only "
    "the shortest contiguous exact quotation from the card that states that reason, at most 23 words. "
    "A vote, an adopted action, or a reason for abstaining is insufficient. Return exactly NONE "
    "if the card does not explicitly state a delegation's reporting purpose."
)
WRITE = (
    "Write one optional sentence of at most 38 words for a neutral record. Use the delivered cards "
    "to identify whether the delegations give the same practical reason for continued reporting. "
    "If so, explicitly name the shared reason using both statements and distinguish that shared "
    "purpose from their votes. Do not infer a delegation's reason from the adoption of a text. "
    "A highlighted quote, if present, is evidence from the associated card. "
    "Return exactly NONE if there is no supported shared reason. End after the sentence."
)


def plan():
    original = previous.locked()
    paths = (Path(__file__), HERE / "protocol.md", PRIOR / "study.py", PRIOR / "plan.json", PRIOR / "score.py",
             PRIOR / "scores.json", HERE.parent / "reason-before-vote/scores.json", RELEASE / "release.json")
    return {
        "pins": {str(path.relative_to(previous.RUNS.parent)): collector.sha(path) for path in paths},
        "checkpoint_index_sha256": original["checkpoint_index_sha256"],
        "cases_in_order": list(VIEWS), "extra_support_cards": list(LOCAL), "expected_physical_calls": 11,
        "extract_prompt": EXTRACT, "chair_prompt": WRITE, "extraction_cap": 55, "chair_cap": 85,
    }


def read(path):
    return json.loads(path.read_text())


def locked():
    config = plan()
    assert config == read(HERE / "plan.json")
    return config


def request(key, cap, system, payload):
    return {"id": key, "max_output_tokens": cap, "messages": [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]}


def admit(reply, text):
    quote = reply["text"]
    if quote == "NONE":
        return ""
    if reply["termination"] == "complete" and 0 < len(quote.split()) <= 23 and quote in text:
        return quote
    return ""


def episode(generate):
    extracted = {}
    for key in LOCAL:
        text = previous.CARDS[key]
        response = generate(request(f"desk/{key}", 55, EXTRACT, {"source": text, "kind": previous.WIRE_KIND[key]}))
        extracted[key] = {"reply": response, "admitted": admit(response, text)}
    cases = {}
    for view, cards in VIEWS.items():
        for arm in ("direct", "quotes"):
            delivered = [{"kind": previous.WIRE_KIND[key], "text": previous.CARDS[key]} for key in cards]
            if arm == "quotes":
                for row, key in zip(delivered, cards, strict=True):
                    if quote := extracted[key]["admitted"]:
                        row["purpose_quote"] = quote
            answer = generate(request(f"{arm}/{view}", 85, WRITE, {"delivered": delivered}))
            cases[f"{arm}/{view}"] = answer
    return {"extractions": extracted, "chair": cases}


def collect(generate, directory):
    def call(spec):
        response = generate(spec)
        collector.suite.append(directory / "calls.jsonl", {"request": spec, "reply": response})
        return response
    (directory / "replies.json").write_text(json.dumps(episode(call), ensure_ascii=False, indent=2) + "\n")


def run():
    locked()
    assert os.environ.get("CUDA_VISIBLE_DEVICES", "").startswith("GPU-")
    with patch.object(collector, "roster", return_value={"reporting-2739": previous.CASE}), patch.object(
        collector, "HERE", HERE), patch.object(collector.suite.e, "HERE", RELEASE), patch.object(
        collector.suite, "collect", collect
    ):
        collector.run(OUT)


def verify():
    from transformers import AutoTokenizer

    config = locked()
    manifest = read(OUT / "complete.json")
    assert set(manifest) == {"calls.jsonl", "launch.json", "tokens.jsonl", "replies.json"}
    assert all(collector.sha(OUT / name) == digest for name, digest in manifest.items())
    launch = read(OUT / "launch.json")
    assert launch["checkpoint_index_sha256"] == config["checkpoint_index_sha256"]
    assert launch["gpu_name"] == "NVIDIA RTX PRO 6000 Blackwell Server Edition"
    assert launch["optimizer_updates"] == 0
    tokenizer = AutoTokenizer.from_pretrained(collector.MODEL, local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    calls, tokens = ([json.loads(line) for line in (OUT / name).read_text().splitlines()]
                     for name in ("calls.jsonl", "tokens.jsonl"))
    assert len(calls) == len(tokens) == config["expected_physical_calls"]
    saved = iter(zip(calls, tokens, strict=True))

    def call(spec):
        info, trace = next(saved)
        assert spec == info["request"] and info["reply"] == trace["response"]
        assert collector.prompt(tokenizer, spec) == trace["input_ids"]
        reply = info["reply"]
        ids = trace["output_ids"]
        assert len(trace["input_ids"]) == reply["input_tokens"]
        assert 0 < len(ids) == reply["output_tokens"] <= spec["max_output_tokens"]
        assert tokenizer.decode(ids, skip_special_tokens=True).strip() == reply["text"]
        assert eos not in ids[:-1] and (ids[-1] == eos) == (reply["termination"] == "complete")
        return reply

    results = episode(call)
    assert next(saved, None) is None and results == read(OUT / "replies.json")
    return {"manifest": manifest, **results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    if mode == "run":
        run()
    else:
        print(json.dumps((plan if mode == "plan" else verify)(), ensure_ascii=False, indent=2))
