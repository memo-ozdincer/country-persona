"""Collect source-local notes and receipt-scoped relation sentences."""
import argparse
import json
from pathlib import Path
import sys
from time import perf_counter
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "tolerance-2686-transfer"))
import live_tolerance as old

base, frozen, prior, READ = old.base, old.frozen, old.prior, old.READ
CASE = READ(HERE / "docket.json")
OUT = HERE / "evidence"
MASKS = (3, 6, 7)
NATIONAL = ("Write an attributed working note of at most 35 words. Keep important named positions "
            "and scope limits. Use only this national evidence. Return only the note.")
PUBLIC = ("Write a compact public paragraph of at most 44 words. Protect draft and resolution "
          "numbers, sponsors, vote, the two main actions and reporting conditions. Return only the paragraph.")
BRIDGE = ("Use only the attributed notes below. Write at most one sentence of no more than 27 words "
          "making a specific source-supported comparison of different or shared positions. "
          "Keep each actor's scope and capacity distinct. Use both relations if possible. "
          "If there is no evidenced comparison, return an empty line.")


def initial():
    return [old.request("public", PUBLIC, {"public": frozen.visible_blocks(CASE["public"])}, 90),
            *[old.request(f"note-{i}", NATIONAL, {"role": role, "recorded_statements": frozen.visible_blocks(source)}, 74)
              for i, (role, source) in enumerate(zip(CASE["roles"], CASE["owned"], strict=True))]]


def bridge(mask, notes):
    visible = [{"speaker": role, "note": text} for i, (role, text) in enumerate(zip(CASE["roles"], notes, strict=True))
               if mask & 1 << i]
    return old.request(f"bridge-{mask}", BRIDGE, {"available": visible}, 60)


def plan():
    inputs = (Path(__file__), HERE / "docket.json", HERE / "protocol.md", HERE / "provenance.json",
              HERE / "join_sources.py", prior.RELEASE / "release.json", Path(base.__file__))
    return {"initial": initial(), "relation_patterns": [bridge(mask, ["<F>", "<R>", "<U>"]) for mask in MASKS],
            "sha256": {str(p.relative_to(prior.STUDY)): prior.digest(p) for p in inputs}}


def collect(generate, directory):
    def run_request(req):
        start = perf_counter()
        reply = generate(req)
        prior.append(directory / "calls.jsonl", {"request": req, "response": reply,
                                                 "elapsed_seconds": perf_counter() - start})
        return reply["text"]
    _, *notes = [run_request(req) for req in initial()]
    for mask in MASKS:
        run_request(bridge(mask, notes))


def run():
    assert plan() == READ(HERE / "plan.json")
    with patch.object(base.suite, "collect", collect), patch.object(
            base, "roster", return_value={CASE["id"]: CASE}), patch.object(
            base, "HERE", HERE), patch.object(base.suite.e, "HERE", prior.RELEASE):
        base.run(OUT)


def compose(fragments):
    result, packets = {}, {}
    for variant in ("verbatim", "compared"):
        for mask in range(8):
            included = ["public", *(f"note-{i}" for i in range(3) if mask & 1 << i)]
            if variant == "compared" and mask in MASKS:
                included.append(f"bridge-{mask}")
            statuses = {fragments[key]["termination"] for key in included}
            if any(not fragments[key]["text"].strip() for key in included if not key.startswith("bridge-")):
                statuses.add("error")
            termination = "error" if "error" in statuses else "cap" if "cap" in statuses else "complete"
            text = "\n\n".join(fragments[key]["text"] for key in included if fragments[key]["text"])
            record = {"text": text, "termination": termination}
            result[f"{variant}/mask-{mask}"] = record
            packet = frozen.final_packet(CASE, [{}, {}, record])
            packets[packet["id"]] = frozen.judge.request(packet)
    return result, dict(sorted(packets.items()))


def verify():
    from transformers import AutoTokenizer

    assert plan() == READ(HERE / "plan.json")
    manifest = READ(OUT / "complete.json")
    assert set(manifest) == {"launch.json", "calls.jsonl", "tokens.jsonl"}
    assert all(prior.digest(OUT / key) == value for key, value in manifest.items())
    launch = READ(OUT / "launch.json")
    assert launch["cases"] == [CASE["id"]] and launch["optimizer_updates"] == 0
    assert launch["protocol_sha256"] == prior.digest(HERE / "protocol.md")
    assert launch["checkpoint_index_sha256"] == prior.digest(base.MODEL / "model.safetensors.index.json")
    tokenizer = AutoTokenizer.from_pretrained(base.MODEL, local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    calls, tokens = [prior.wire.n.lines(OUT / name) for name in ("calls.jsonl", "tokens.jsonl")]
    notes = [row["response"]["text"] for row in calls[1:4]]
    expected = initial() + [bridge(mask, notes) for mask in MASKS]
    fragments = {}
    for req, row, trace in zip(expected, calls, tokens, strict=True):
        out = row["response"]
        assert req == row["request"] and trace["input_ids"] == base.prompt(tokenizer, req)
        assert trace["response"] == out and len(trace["output_ids"]) == out["output_tokens"]
        assert tokenizer.decode(trace["output_ids"], skip_special_tokens=True).strip() == out["text"]
        assert bool(trace["output_ids"] and trace["output_ids"][-1] == eos) == (out["termination"] == "complete")
        fragments[req["id"]] = out | {"elapsed_seconds": row["elapsed_seconds"]}
    results, packets = compose(fragments)
    return {"fragments": fragments, "records": results, "blind_packets": packets, "sha256": manifest}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    if mode == "run":
        run()
    else:
        frozen.emit({"plan": plan, "verify": verify}[mode]())
