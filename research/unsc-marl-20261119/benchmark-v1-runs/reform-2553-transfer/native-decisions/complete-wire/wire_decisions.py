"""Replay the locked receipt game using complete-message likelihoods."""
import argparse
import json
from pathlib import Path
import sys
from time import perf_counter
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
sys.path.insert(0, str(PARENT))
import live_choices as old

wire, base, case, prior = old.prior.wire, old.base, old.case, old.prior
READ, frozen, CASE = old.READ, old.frozen, old.CASE
OUT = HERE / "evidence"
FORMS = wire.forms


def menu(request):
    return list(json.loads(request["messages"][-1]["content"])["output_alias_to_your_card"])


def forms(items):
    return [item for item in FORMS(items) if len(item["ids"]) == 1]


def converted(req, forecast=None):
    payload = json.loads(req["messages"][-1]["content"])
    actions = payload.pop("letter_to_your_card")
    payload["output_alias_to_your_card"] = {"1": actions["A"], "2": actions["B"]}
    if forecast is not None:
        payload["public_independent_desk_forecast"] = forecast
    assert req["messages"][0]["content"].endswith("Return one answer letter.")
    text = req["messages"][0]["content"].removesuffix("Return one answer letter.") + (
        "Return only a JSON array containing one output alias from the supplied mapping.")
    return {
        "id": ("forecast/" if forecast is not None else "") + req["id"], "max_output_tokens": 48,
        "messages": [{"role": "system", "content": text},
                     {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]}


def plan():
    initial = READ(PARENT / "plan.json")["requests"]
    archive = READ(PARENT.parent / "results.json")["orders"]["uk_later"]["forced_private_inventory"]
    ref, = [row for row in archive if row["first_card_probability"] == old.SHARE and row["receipt"] == .95]
    independent = ref["outcomes"]["content"]["fixed"]["third"] + 1
    forecast = {"owner": "Belgium", "card_probability": {str(i): float(i == independent) for i in (1, 2)},
                "source": "public forecast, not an observation of a sent or delivered card"}
    ordinary = [converted(req) for req in initial]
    targeted = [converted(req, forecast) for req in initial if req["id"].startswith("uk_later/0.95/")
                and "/independent/" not in req["id"]]
    assert len(ordinary) == 48 and len(targeted) == 10
    all_requests = ordinary + targeted
    counts = [sum(len(row["forms"]) for row in forms(menu(req))) for req in all_requests]
    assert sum(counts) <= 600
    pins = (Path(__file__), HERE / "protocol.md", PARENT / "plan.json", PARENT / "verified.json",
            PARENT / "score_native.py", PARENT.parent / "results.json",
            Path(wire.__file__), Path(base.__file__))
    return {"requests": all_requests, "candidate_counts": counts,
            "sha256": {str(p.relative_to(prior.STUDY)): prior.digest(p) for p in pins}}


def collect(generate, directory):
    wire.STATE["used"] = 0
    for req in plan()["requests"]:
        wire.STATE["request"] = req
        started = perf_counter()
        result = generate(req)
        assert result["termination"] == "complete"
        prior.append(directory / "calls.jsonl", {"request": req, "response": result,
                                                 "elapsed_seconds": perf_counter() - started})
        prior.append(directory / "likelihood.jsonl", wire.STATE.pop("last"))


def run():
    assert plan() == READ(HERE / "plan.json")
    worker = base.run

    def launch(directory):
        with patch.object(base, "roster", return_value={CASE["id"]: CASE}):
            worker(directory)

    with patch.object(wire, "OUT", OUT), patch.object(wire, "collect", collect), patch.object(
            wire, "forms", forms), patch.object(wire.s, "menu", menu), patch.object(
            base, "run", launch), patch.object(base.suite.e, "HERE", prior.RELEASE), patch.object(base, "HERE", HERE):
        wire.run()


def verify():
    from transformers import AutoTokenizer

    locked = plan()
    assert locked == READ(HERE / "plan.json")
    manifest = READ(OUT / "complete.json")
    assert set(manifest) == {"launch.json", "calls.jsonl", "likelihood.jsonl", "tokens.jsonl"}
    assert all(prior.digest(OUT / name) == value for name, value in manifest.items())
    launch = READ(OUT / "launch.json")
    assert launch["cases"] == [CASE["id"]] and launch["optimizer_updates"] == 0
    assert launch["checkpoint_index_sha256"] == prior.digest(base.MODEL / "model.safetensors.index.json")
    assert launch["protocol_sha256"] == prior.digest(HERE / "protocol.md")
    tok = AutoTokenizer.from_pretrained(base.MODEL, local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    calls, scores, tokens = [wire.n.lines(OUT / name) for name in ("calls.jsonl", "likelihood.jsonl", "tokens.jsonl")]
    verified = {}
    for req, n, row, alternatives, trace in zip(locked["requests"], locked["candidate_counts"],
                                                 calls, scores, tokens, strict=True):
        assert req == row["request"] == alternatives["request"]
        assert trace["input_ids"] == base.prompt(tok, req)
        candidates = alternatives["candidates"]
        assert [{**item, "forms": [f["text"] for f in item["forms"]]} for item in candidates] == forms(menu(req))
        flattened = [item for group in candidates for item in group["forms"]]
        assert len(flattened) == n
        for item in flattened:
            assert tok.encode(item["text"], add_special_tokens=False) + [eos] == item["tokens"]
        summary = wire.summarize(candidates)
        assert summary == alternatives["selection"] and summary["selected"] == row["response"]["text"]
        assert row["response"] == trace["response"]
        assert tok.encode(summary["selected"], add_special_tokens=False) + [eos] == trace["output_ids"]
        verified[req["id"]] = {"candidate_scores": summary, "input_tokens": row["response"]["input_tokens"],
                               "output_tokens": row["response"]["output_tokens"],
                               "elapsed_seconds": row["elapsed_seconds"]}
    return {"outputs": verified, "candidate_sequences": sum(locked["candidate_counts"]),
            "evidence_sha256": manifest}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    if mode == "run":
        run()
    else:
        frozen.emit({"plan": plan, "verify": verify}[mode]())
