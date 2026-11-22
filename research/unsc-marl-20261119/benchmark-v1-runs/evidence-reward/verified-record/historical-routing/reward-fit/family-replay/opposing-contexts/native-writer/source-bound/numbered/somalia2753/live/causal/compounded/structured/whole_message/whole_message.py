"""Score complete role-local wire messages and emit canonical IDs."""
import argparse
from hashlib import sha256
from itertools import permutations
import json
from math import exp, fsum, log
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import structured_live as s

e, n, g, w = s.e, s.n, s.g, s.w
OUT = HERE / "evidence"
LIMIT = 600
STATE = {}


def forms(menu):
    result = []
    for size in range(len(menu) + 1):
        for value in permutations(menu, size):
            canonical = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            encodings = [value]
            if all(i.isdecimal() and i == str(int(i)) for i in value):
                encodings.append(tuple(int(i) for i in value))
            forms = {}
            for row in encodings:
                for text in (json.dumps(row, ensure_ascii=False), json.dumps(row, ensure_ascii=False, separators=(",", ":"))):
                    forms[text] = None
                    forms["```json\n" + text + "\n```"] = None
            result.append({"ids": list(value), "canonical": canonical, "forms": list(forms)})
    return result


def summarize(candidates):
    groups = []
    for row in candidates:
        values = [item["logp"] for item in row["forms"]]
        peak = max(values)
        mass = peak + log(fsum(exp(value - peak) for value in values))
        canonical = next(item["logp"] for item in row["forms"] if item["text"] == row["canonical"])
        groups.append({"ids": row["ids"], "canonical": row["canonical"],
                       "log_mass": mass, "canonical_logp": canonical})
    return {"selected": max(groups, key=lambda r: r["log_mass"])["canonical"],
            "canonical_only": max(groups, key=lambda r: r["canonical_logp"])["canonical"],
            "alternatives": groups}


def plan():
    original = s.plan()
    requests = original["reference_requests"]
    counts = [sum(len(r["forms"]) for r in forms(s.menu(req))) for req in requests]
    assert sum(counts) <= LIMIT
    pins = (Path(__file__), HERE / "protocol.md", Path(s.__file__), HERE.parent / "plan.json")
    return {"candidate_budget": LIMIT, "requests": requests, "expected_candidate_counts": counts,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in pins}}


def collect(generate, directory):
    assert plan() == n.read(HERE / "plan.json")
    STATE["used"] = 0

    def tracked(request):
        STATE["request"] = request
        result = generate(request)
        evidence = STATE.pop("last")
        n.base.suite.append(directory / "calls.jsonl", {"request": request, "response": result})
        n.base.suite.append(directory / "likelihood.jsonl", evidence)
        return result

    result = s.transfer(tracked)
    (directory / "dispatch.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")


def run():
    import torch
    from transformers import AutoTokenizer
    from transformers.generation.utils import GenerationMixin

    tok = AutoTokenizer.from_pretrained(n.base.MODEL, local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")

    def select(model, *args, **kw):
        request = STATE.pop("request")
        prompt = kw["input_ids"]
        assert prompt[0].tolist() == n.base.prompt(tok, request)
        prefix = prompt.shape[-1]
        candidates = forms(s.menu(request))
        flat = []
        for candidate in candidates:
            candidate["forms"] = [{"text": text, "tokens": tok.encode(text, add_special_tokens=False) + [eos]}
                                  for text in candidate["forms"]]
            flat.extend(candidate["forms"])
        STATE["used"] += len(flat)
        assert STATE["used"] <= LIMIT
        widest = max(len(row["tokens"]) for row in flat)
        assert widest <= request["max_output_tokens"]
        device = prompt.device
        pos = torch.arange(prefix - 1, prefix + widest - 1, device=device)
        for offset in range(0, len(flat), 8):
            batch = flat[offset:offset + 8]
            follow = torch.full((len(batch), widest), tok.pad_token_id, device=device, dtype=prompt.dtype)
            mask = torch.zeros((len(batch), prefix + widest), device=device, dtype=prompt.dtype)
            mask[:, :prefix] = 1
            for i, row in enumerate(batch):
                ids = row["tokens"]
                follow[i, :len(ids)] = torch.tensor(ids, device=device, dtype=prompt.dtype)
                mask[i, prefix:prefix + len(ids)] = 1
            inputs = torch.cat((prompt.expand(len(batch), -1), follow), dim=-1)
            logits = model(input_ids=inputs, attention_mask=mask, use_cache=False, logits_to_keep=pos).logits
            log_probability = logits.float().log_softmax(-1).gather(-1, follow.unsqueeze(-1))[:, :, 0]
            for i, row in enumerate(batch):
                row["logp"] = float(log_probability[i, :len(row["tokens"])].sum().item())
        summary = summarize(candidates)
        STATE["last"] = {"request": request, "candidates": candidates, "selection": summary}
        response = tok.encode(summary["selected"], add_special_tokens=False) + [eos]
        return torch.cat((prompt, torch.tensor([response], device=device, dtype=prompt.dtype)), dim=-1)

    with patch.object(GenerationMixin, "generate", select), patch.object(
            n.base.suite, "collect", collect), patch.object(
            n.base, "roster", return_value={"somalia-complete-message-decoder": None}):
        n.base.run(OUT)


def verify():
    from tokenizers import Tokenizer

    assert plan() == n.read(HERE / "plan.json")
    manifest = n.read(OUT / "complete.json")
    assert set(manifest) == {"calls.jsonl", "tokens.jsonl", "launch.json", "dispatch.json", "likelihood.jsonl"}
    assert all(sha256((OUT / name).read_bytes()).hexdigest() == val for name, val in manifest.items())
    actual_read = n.read

    def disk(path):
        if path == OUT / "complete.json":
            return {k: v for k, v in manifest.items() if k in ("calls.jsonl", "tokens.jsonl", "launch.json")}
        return actual_read(path)

    def calls():
        return n.lines(OUT / "calls.jsonl")

    with patch.object(n, "OUT", OUT), patch.object(n, "read", disk), patch.object(s.t.LIB.audit, "calls", calls):
        verification = s.t.LIB.audit.verify()
    tokenizer = Tokenizer.from_file(str(n.base.MODEL / "tokenizer.json"))
    eos = tokenizer.token_to_id("<|im_end|>")
    totals = []
    for exam, call in zip(n.lines(OUT / "likelihood.jsonl"), calls(), strict=True):
        assert exam["request"] == call["request"]
        measured = exam["candidates"]
        assert [{**r, "forms": [v["text"] for v in r["forms"]]} for r in measured] == forms(s.menu(call["request"]))
        for choice in measured:
            for row in choice["forms"]:
                assert tokenizer.encode(row["text"], add_special_tokens=False).ids + [eos] == row["tokens"]
        assert summarize(measured) == exam["selection"]
        assert exam["selection"]["selected"] == call["response"]["text"]
        totals.append(sum(len(row["forms"]) for row in measured))

    logged = iter(calls())

    def read(request):
        row = next(logged)
        assert request == row["request"]
        return row["response"]

    assert json.loads(json.dumps(s.transfer(read))) == n.read(OUT / "dispatch.json")
    assert next(logged, None) is None
    return verification | {"candidates_per_request": totals, "scored_candidates": sum(totals),
                           "semantic_selection_replayed": True, "dispatch_replayed": True}


def score():
    with patch.object(w, "OUT", OUT), patch.object(g, "HERE", HERE):
        return g.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify", "score"))
    mode = parser.parse_args().mode
    if mode == "run":
        run()
    else:
        e.emit({"plan": plan, "verify": verify, "score": score}[mode]())
