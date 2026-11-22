"""Test role-local validity, uniqueness and termination against real checkpoint tokens."""
import json
from math import factorial
from pathlib import Path

from tokenizers import Tokenizer

import passage_codec as c
import structured_live as r


def probe():
    tokenizer = Tokenizer.from_file(str(r.n.base.MODEL / "tokenizer.json"))
    eos = tokenizer.token_to_id("<|im_end|>")
    encode = lambda text: tokenizer.encode(text, add_special_tokens=False).ids
    decode = lambda ids: tokenizer.decode(list(ids), skip_special_tokens=False)
    scenarios = {}
    for request in r.plan()["reference_requests"]:
        ids = r.menu(request)
        tree, total, longest = c.build(ids, encode, decode, eos)
        assert total == sum(factorial(len(ids)) // factorial(len(ids) - k) for k in range(len(ids) + 1))
        valid = ([], list(ids), list(reversed(ids)))
        for value in valid:
            text = json.dumps(value, separators=(",", ":"))
            canonical = encode(text)
            assert c.validate(ids, text) == value
            assert eos in c.allowed(tree, canonical)
            assert c.allowed(tree, canonical + [eos]) == []
        invalid = ('[\"999\"]', '[7]', json.dumps([ids[0], ids[0]], separators=(",", ":")),
                   '[] trailing', '```json\n[]\n```', '[', '[]\n[]')
        for message in invalid:
            try:
                c.validate(ids, message)
            except ValueError:
                pass
            else:
                raise AssertionError(message)
            try:
                remainder = c.allowed(tree, encode(message))
            except ValueError:
                continue
            assert eos not in remainder, message
        payload = json.loads(request["messages"][-1]["content"])
        scenarios[f"{payload['speaker']}/{payload['stage']}/{payload['heard_question']}"] = {
            "menu": ids, "allowed_strings": total, "max_output_tokens_including_eos": longest,
            "negative_controls": len(invalid), "positive_controls": len(valid)}
    stored = r.n.read(r.HERE / "plan.json")
    assert r.plan() == stored
    sample = {"china": ["9", "2"], "somalia": ["8", "5"], "us": ["73"]}
    planned = {r.e.checksum(req) for req in stored["reference_requests"]}

    def fake_generate(request):
        assert r.e.checksum(request) in planned
        data = json.loads(request["messages"][-1]["content"])
        return {"text": json.dumps(sample[data["speaker"]], separators=(",", ":")), "termination": "complete"}

    rehearsal = r.transfer(fake_generate)
    receipts = {arm: row["receipt"] for arm, row in rehearsal["arms"].items()}
    assert receipts == r.n.read(r.c.HERE.parent / "plan.json")["expected_receipts"]
    return {"grammar_cases": scenarios, "rehearsal_receipts": receipts}


if __name__ == "__main__":
    r.e.emit(probe())
