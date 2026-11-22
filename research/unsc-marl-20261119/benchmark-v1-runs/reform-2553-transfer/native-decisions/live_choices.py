"""Collect native receipt-conditioned decisions from two language-model desks."""
import argparse
from importlib.util import module_from_spec, spec_from_file_location
from itertools import product
import json
from math import isfinite
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
spec = spec_from_file_location("reform_2553_native_locked_case", PARENT / "transfer.py")
case = module_from_spec(spec)
spec.loader.exec_module(case)

READ, old, frozen = case.READ, case.old, case.frozen
prior, base = old.tribunals, old.tribunals.wire.n.base
CASE = case.CASE
OUT = HERE / "evidence"
RATES = (.55, .95)
SHARE = .75
VIEWS = ("absent", "card1", "card2", "arrived", "none")
LABELS = {"ab": {"A": "1", "B": "2"}, "ba": {"A": "2", "B": "1"}}
SYSTEM = (
    "Choose one passage from your assigned desk for a source-faithful UN decision record. "
    "Maximize the expected documentary points. A standalone score is earned if your card reaches the chair. "
    "A joint bonus requires both listed cards to reach the chair. Delivery events for the three desks "
    "are independent. Before choosing, use any observed early-desk receipt literally. "
    "A third desk does not see the later desk's choice and vice versa. "
    "If you are unsure how another desk will choose, use their available information and expected coverage. "
    "The numerical menu is an evaluation device. Never invent a passage. Return one answer letter."
)


def requests():
    for order, rate in product(case.ORDERS, RATES):
        permutation = case.ORDERS[order]
        roles = [CASE["roles"][i] for i in permutation]
        menus = [CASE["owned"][i] for i in permutation]
        weights = {item["id"]: item["weight"] for item in CASE["rubric"]}
        codes = {r["id"]: f"{role} card {j+1}" for role, menu in zip(roles, menus, strict=True)
                 for j, r in enumerate(menu)}
        announced = {role: {str(i+1): weights[card["id"]] for i, card in enumerate(menu)}
                     for role, menu in zip(roles, menus, strict=True)}
        shared = {"resolution": "S/RES/2553 (2020)", "roles": {"early": roles[1], "later": roles[0], "independent": roles[2]},
                  "early_card_prior": {"1": SHARE, "2": 1. - SHARE},
                  "receipt_probability_per_desk": rate,
                  "standalone_points": announced,
                  "joint_requirements": [{"cards": [codes[x] for x in r["needs"]], "extra": weights[r["id"]]}
                                         for r in CASE["relations"]]}
        observations = {
            "absent": {"early_receipt": "did not arrive"},
            "card1": {"early_receipt": "arrived", "card": "1", "owner": roles[1], "text": menus[1][0]["text"]},
            "card2": {"early_receipt": "arrived", "card": "2", "owner": roles[1], "text": menus[1][1]["text"]},
            "arrived": {"early_receipt": "arrived", "card": "not shown"},
            "none": {"early_receipt": "no observation"},
        }
        for view, mapping in product((*VIEWS, "independent"), LABELS):
            local = 2 if view == "independent" else 0
            data = {**shared, "your_desk": roles[local],
                    "your_menu": {str(i+1): card["text"] for i, card in enumerate(menus[local])},
                    "your_view": {"early_receipt": "no observation"} if local == 2 else observations[view],
                    "letter_to_your_card": LABELS[mapping]}
            yield {"id": f"{order}/{rate}/{view}/{mapping}", "max_output_tokens": 2,
                   "messages": [{"role": "system", "content": SYSTEM},
                                {"role": "user", "content": json.dumps(data, ensure_ascii=False)}]}


def plan():
    files = (Path(__file__), HERE / "protocol.md", PARENT / "docket.json", PARENT / "plan.json",
             PARENT / "results.json", PARENT / "component.json", prior.RELEASE / "release.json", Path(base.__file__))
    rows = list(requests())
    assert len(rows) == 48
    return {"requests": rows, "rates": list(RATES), "staffing_prior": SHARE,
            "sha256": {str(p.relative_to(prior.STUDY)): prior.digest(p) for p in files}}


def token_choices(tokenizer):
    ids = {letter: tokenizer.encode(letter, add_special_tokens=False) for letter in ("A", "B")}
    assert all(len(v) == 1 for v in ids.values()) and ids["A"] != ids["B"]
    return {letter: value[0] for letter, value in ids.items()}


def run():
    import torch
    from transformers import AutoTokenizer
    from transformers.generation.utils import GenerationMixin

    locked = plan()
    assert locked == READ(HERE / "plan.json")
    tokenizer = AutoTokenizer.from_pretrained(base.MODEL, local_files_only=True)
    choices = token_choices(tokenizer)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    state = {}

    def choose(model, *args, **kwargs):
        prompt = kwargs["input_ids"]
        assert prompt[0].tolist() == base.prompt(tokenizer, state["request"])
        scores = model(input_ids=prompt, attention_mask=kwargs["attention_mask"],
                       use_cache=False, logits_to_keep=1).logits[0, -1].float()
        logits = dict(zip(choices, scores[list(choices.values())].tolist(), strict=True))
        state["logits"] = logits
        label = max(logits, key=logits.get)
        result = torch.tensor([[choices[label], eos]], device=prompt.device, dtype=prompt.dtype)
        return torch.cat((prompt, result), dim=-1)

    def collect(generate, directory):
        for req in locked["requests"]:
            state["request"] = req
            stamp = perf_counter()
            response = generate(req)
            logits = state.pop("logits")
            assert response["text"] == max(logits, key=logits.get) and response["termination"] == "complete"
            prior.append(directory / "calls.jsonl", {"request": req, "response": response, "logits": logits,
                                                     "elapsed_seconds": perf_counter() - stamp})

    with patch.object(GenerationMixin, "generate", choose), patch.object(base.suite, "collect", collect), patch.object(
            base, "roster", return_value={CASE["id"]: CASE}), patch.object(
            base, "HERE", HERE), patch.object(base.suite.e, "HERE", prior.RELEASE):
        base.run(OUT)


def verify():
    from transformers import AutoTokenizer

    locked = plan()
    assert locked == READ(HERE / "plan.json")
    manifest = READ(OUT / "complete.json")
    assert set(manifest) == {"launch.json", "calls.jsonl", "tokens.jsonl"}
    assert all(prior.digest(OUT / name) == digest for name, digest in manifest.items())
    launch = READ(OUT / "launch.json")
    assert launch["cases"] == [CASE["id"]] and launch["optimizer_updates"] == 0
    assert launch["protocol_sha256"] == prior.digest(HERE / "protocol.md")
    assert launch["checkpoint_index_sha256"] == prior.digest(base.MODEL / "model.safetensors.index.json")
    tok = AutoTokenizer.from_pretrained(base.MODEL, local_files_only=True)
    allowed = token_choices(tok)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    calls, tokens = [prior.wire.n.lines(OUT / name) for name in ("calls.jsonl", "tokens.jsonl")]
    rows = {}
    for req, row, trace in zip(locked["requests"], calls, tokens, strict=True):
        logits = row["logits"]
        assert row["request"] == req and trace["input_ids"] == base.prompt(tok, req)
        assert row["response"] == trace["response"] and set(logits) == set(allowed)
        assert all(isfinite(v) for v in logits.values())
        label = max(logits, key=logits.get)
        assert trace["output_ids"] == [allowed[label], eos] and row["response"]["text"] == label
        rows[req["id"]] = {"label": label, "logits": logits, "response": row["response"],
                          "elapsed_seconds": row["elapsed_seconds"]}
    return {"outputs": rows, "evidence_sha256": manifest}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    if mode == "run":
        run()
    else:
        frozen.emit({"plan": plan, "verify": verify}[mode]())
