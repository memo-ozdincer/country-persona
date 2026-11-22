"""Replay the scope-bound native follow-up and apply the same final scorer."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import scoped as trial
import fixed_alternative

m, review, e = trial.m, trial.review, trial.e
HERE = Path(__file__).resolve().parent


def rows(name):
    return [json.loads(line) for line in (trial.RUN / name).read_text().splitlines()]


def verify():
    from jinja2.sandbox import ImmutableSandboxedEnvironment
    from tokenizers import Tokenizer

    digest = review.digest
    expected = e.read(trial.RUN / "complete.json")
    assert set(expected) == {"calls.jsonl", "trace.jsonl", "tokens.jsonl", "inputs.json", "launch.json"}
    assert all(digest(trial.RUN / name) == value for name, value in expected.items())
    assert trial.pins() == e.read(trial.RUN / "inputs.json")
    assert trial.plan() == e.read(HERE / "plan.json")
    prior = e.read(m.RUN / "launch.json")
    launch = e.read(trial.RUN / "launch.json")
    for field in ("checkpoint", "checkpoint_index_sha256", "decoding", "dtype", "attention", "gpu_name", "optimizer_updates"):
        assert prior[field] == launch[field]
    model = Path(launch["checkpoint"])
    assert digest(model / "model.safetensors.index.json") == launch["checkpoint_index_sha256"]
    tok = Tokenizer.from_file(str(model / "tokenizer.json"))
    tmpl = ImmutableSandboxedEnvironment(trim_blocks=True, lstrip_blocks=True).from_string(
        (model / "chat_template.jinja").read_text())
    eos = tok.token_to_id("<|im_end|>")
    saved = iter(zip(rows("calls.jsonl"), rows("tokens.jsonl"), strict=True))

    def generate(req):
        call, tokens = next(saved)
        assert req == call["request"] and call["reply"] == tokens["response"]
        text = tmpl.render(messages=req["messages"], enable_thinking=False, add_generation_prompt=True, tools=None)
        inp = tok.encode(text, add_special_tokens=False).ids
        answer, out = call["reply"], tokens["output_ids"]
        assert inp == tokens["input_ids"] and len(inp) == answer["input_tokens"]
        assert out and len(out) == answer["output_tokens"] <= req["max_output_tokens"] and eos not in out[:-1]
        assert (out[-1] == eos) == (answer["termination"] == "complete")
        assert tok.decode(out, skip_special_tokens=True).strip() == answer["text"]
        return answer

    trace, reusable, novel = trial.execute(generate)
    assert trace == rows("trace.jsonl") and next(saved, None) is None
    fault = trial.plan()["new_requests"][0]
    altered = {"termination": "complete", "text": '{"card":"russia","quote":"Unsupported claim."}'}
    assert not trial.admit(altered, fault)
    return {"new_native_calls": len(novel), "reused_exact_native_prompts": len(reusable),
            "bound_quote_rejects_corruption": True, "optimizer_updates": launch["optimizer_updates"]}


def compare_alternative(scores_dir):
    read = review.read_lines
    def both(name):
        if name == "calls.jsonl":
            return [*read(name), *rows(name)]
        return rows(name)
    with patch.object(review, "read_lines", both), patch.object(m, "validate", trial.admit), patch.object(
            fixed_alternative, "HERE", scores_dir):
        return fixed_alternative.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("verify", "packets", "score", "alternative"))
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    mode = args.mode
    form = "compact" if args.compact else "exact"
    if mode == "verify":
        e.emit(verify())
    elif mode == "alternative":
        e.emit(compare_alternative(HERE / "compact-scores" if args.compact else HERE))
    else:
        with patch.object(review, "read_lines", rows):
            if mode == "packets":
                e.emit(review.deck(form)[1])
            else:
                # Score reads its marks independently from the rendering module's sources.
                if args.compact:
                    scorer = review.score
                    with patch.object(review, "deck", return_value=review.deck(form)), patch.object(
                            review, "HERE", HERE / "compact-scores"):
                        e.emit(scorer(form))
                else:
                    with patch.object(review, "HERE", HERE):
                        e.emit(review.score(form))
