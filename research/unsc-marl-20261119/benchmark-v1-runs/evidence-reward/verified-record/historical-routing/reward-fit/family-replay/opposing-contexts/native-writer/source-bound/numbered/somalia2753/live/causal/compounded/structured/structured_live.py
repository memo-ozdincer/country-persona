"""Execute the complete Somalia witness under role-local token constraints."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import compound_reply as c
import audit_live as audit
import passage_codec as codec

w, e, t, n, g = c.w, c.e, c.t, c.n, c.g
OUT = HERE / "evidence"


def translate(prompt):
    return c.new_request(prompt) if c.target_prompt(prompt) else prompt


def menu(request):
    payload = json.loads(request["messages"][-1]["content"])
    return tuple(payload["passages"])


def transfer(generate):
    def constrained(original):
        prompt = translate(original)
        reply = generate(prompt)
        assert reply["termination"] == "complete"
        selected = codec.validate(menu(prompt), reply["text"])
        if c.target_prompt(original):
            return reply | {"text": json.dumps([i for key in selected for i in c.EXPANSION[key]])}
        return reply

    with patch.object(w, "settings", c.c.settings):
        return w.simulate(constrained)


def plan():
    parent = n.read(c.HERE.parent / "plan.json")
    requests = [translate(row) for row in parent["requests"]]
    assert len({e.checksum(r) for r in requests}) == len(requests)
    files = (Path(__file__), HERE / "protocol.md", Path(codec.__file__), c.HERE / "plan.json",
             c.HERE.parent / "plan.json", Path(c.__file__), Path(w.__file__))
    return {"physical_request_limit": w.LIMIT, "reference_requests": requests,
            "sha256": {str(file.relative_to(HERE.parents[2])): sha256(file.read_bytes()).hexdigest()
                       for file in files}}


def collect(generate, directory):
    assert plan() == n.read(HERE / "plan.json")

    def logged(request):
        # An upstream abstention can reach a different planned policy state.
        # Its route is logged and subject to the same candidate construction.
        register(request)
        response = generate(request)
        n.base.suite.append(directory / "calls.jsonl", {"request": request, "response": response})
        return response

    trace = transfer(logged)
    (directory / "dispatch.json").write_text(json.dumps(trace, indent=2, ensure_ascii=False) + "\n")


active = {}


def register(request):
    active["request"] = request


def run():
    from transformers import AutoTokenizer
    from transformers.generation.utils import GenerationMixin

    tokenizer = AutoTokenizer.from_pretrained(n.base.MODEL, local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    native_generate = GenerationMixin.generate

    def constrained_generate(model, *args, **kw):
        req = active.pop("request")
        input_ids = kw["input_ids"]
        prefix_length = input_ids.shape[-1]
        assert input_ids[0].tolist() == n.base.prompt(tokenizer, req)
        tree, _, longest = codec.build(menu(req), lambda s: tokenizer.encode(s, add_special_tokens=False),
                                       lambda ids: tokenizer.decode(list(ids), skip_special_tokens=False), eos)
        assert longest <= req["max_output_tokens"]

        def permit(batch_id, tokens):
            assert batch_id == 0
            return codec.allowed(tree, tokens[prefix_length:].tolist())

        return native_generate(model, *args, prefix_allowed_tokens_fn=permit, **kw)

    with patch.object(GenerationMixin, "generate", constrained_generate), patch.object(
            n.base.suite, "collect", collect), patch.object(
            n.base, "roster", return_value={"somalia-role-local-constrained-generation": None}):
        n.base.run(OUT)


def verify():
    from tokenizers import Tokenizer

    assert plan() == n.read(HERE / "plan.json")
    manifest = n.read(OUT / "complete.json")
    assert set(manifest) == {"dispatch.json", "calls.jsonl", "tokens.jsonl", "launch.json"}
    assert all(sha256((OUT / name).read_bytes()).hexdigest() == val for name, val in manifest.items())
    disk = n.read

    def metric_read(path):
        if path == OUT / "complete.json":
            return {k: v for k, v in manifest.items() if k != "dispatch.json"}
        return disk(path)

    def calls():
        return n.lines(OUT / "calls.jsonl")

    with patch.object(n, "OUT", OUT), patch.object(n, "read", metric_read), patch.object(
            t.LIB.audit, "calls", calls):
        receipts = t.LIB.audit.verify()
    tokenizer = Tokenizer.from_file(str(n.base.MODEL / "tokenizer.json"))
    eos = tokenizer.token_to_id("<|im_end|>")
    widths = []
    for row, tokens in zip(calls(), n.lines(OUT / "tokens.jsonl"), strict=True):
        tree, paths, _ = codec.build(menu(row["request"]), lambda s: tokenizer.encode(s, add_special_tokens=False).ids,
                                      lambda x: tokenizer.decode(list(x), skip_special_tokens=False), eos)
        out = tokens["output_ids"]
        assert out[-1] == eos and not codec.allowed(tree, out)
        codec.validate(menu(row["request"]), row["response"]["text"])
        widths.append(paths)
    trace = iter(calls())

    def cached(prompt):
        original = next(trace)
        assert prompt == original["request"]
        return original["response"]

    assert json.loads(json.dumps(transfer(cached))) == n.read(OUT / "dispatch.json")
    assert next(trace, None) is None
    return receipts | {"grammar_paths_by_call": widths, "dispatch_replayed": True}


def score():
    with patch.object(w, "OUT", OUT), patch.object(g, "HERE", HERE):
        return g.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify", "score"))
    command = parser.parse_args().mode
    if command == "run":
        run()
    else:
        e.emit({"plan": plan, "verify": verify, "score": score}[command]())
