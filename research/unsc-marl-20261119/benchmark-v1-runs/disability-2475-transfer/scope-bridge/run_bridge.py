"""Cross original and restored notes with two comparison prompts."""
import argparse
from itertools import product
import json
from pathlib import Path
import sys
from time import perf_counter
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
sys.path.insert(0, str(PARENT))
import live_2475 as original

CASE, READ, base = original.CASE, original.READ, original.base
prior, frozen, request = original.prior, original.frozen, original.old.request
OUT = HERE / "evidence"
SCOPE = (
    "Use only the attributed notes below. Before writing, identify the speaker, action, and exact object "
    "of each position. Keep an interpretation of a provision in one instrument separate from a view "
    "on a different instrument, even if they share a number or topic. Do not infer a view on a claim "
    "from agreement on another claim. Prefer two different sources for comparisons. "
    "Return one sentence of at most 27 words giving the most precise evidenced comparison, or an empty line."
)


def fragments():
    old = READ(PARENT / "verified.json")["fragments"]
    authored = READ(PARENT / "oracle.json")["authored_records"]["7"]["answer"].split("\n\n")
    assert len(authored) == 5
    return {"native": [old[k] for k in ("public", "note-0", "note-1", "note-2")],
            "authored": [{"text": text, "termination": "complete"} for text in authored[:4]]}


def requests():
    for arm, fragments_ in fragments().items():
        notes = [row["text"] for row in fragments_[1:]]
        for mask, method in product(original.MASKS, ("plain", "scope")):
            old = original.bridge(mask, notes)
            command = original.BRIDGE if method == "plain" else SCOPE
            data = json.loads(old["messages"][1]["content"])
            control = request(f"{arm}/{method}/{mask}", command, data, 60)
            assert control["messages"][1] == old["messages"][1]
            yield control


def plan():
    inputs = (Path(__file__), HERE / "protocol.md", PARENT / "docket.json", PARENT / "verified.json",
              PARENT / "oracle.json", PARENT / "evidence/calls.jsonl", PARENT / "live_2475.py",
              prior.RELEASE / "release.json", Path(base.__file__))
    return {"requests": list(requests()), "reused": [f"native/plain/{m}" for m in original.MASKS],
            "sha256": {str(p.relative_to(prior.STUDY)): prior.digest(p) for p in inputs}}


def collect(generate, directory):
    for req in requests():
        if not req["id"].startswith("native/plain"):
            clock = perf_counter()
            result = generate(req)
            prior.append(directory / "calls.jsonl", {"request": req, "response": result,
                                                     "elapsed_seconds": perf_counter() - clock})


def run():
    assert plan() == READ(HERE / "plan.json")
    with patch.object(base.suite, "collect", collect), patch.object(
            base, "roster", return_value={CASE["id"]: CASE}), patch.object(
            base, "HERE", HERE), patch.object(base.suite.e, "HERE", prior.RELEASE):
        base.run(OUT)


def compose(bridges):
    records, packets = {}, {}
    for bank, notes in fragments().items():
        for method, mask in product(("none", "plain", "scope"), range(8)):
            selected = [notes[0], *(notes[i + 1] for i in range(3) if mask & 1 << i)]
            if method != "none" and mask in original.MASKS:
                selected.append(bridges[f"{bank}/{method}/{mask}"])
            statuses = {row["termination"] for row in selected}
            status = "error" if "error" in statuses else "cap" if "cap" in statuses else "complete"
            text = "\n\n".join(row["text"] for row in selected if row["text"])
            record = {"text": text, "termination": status}
            records[f"{bank}/{method}/mask-{mask}"] = record
            packet = frozen.final_packet(CASE, [{}, {}, record])
            packets[packet["id"]] = frozen.judge.request(packet)
    return records, dict(sorted(packets.items()))


def verify():
    from transformers import AutoTokenizer

    expected = plan()
    assert expected == READ(HERE / "plan.json")
    manifest = READ(OUT / "complete.json")
    assert set(manifest) == {"launch.json", "calls.jsonl", "tokens.jsonl"}
    assert all(prior.digest(OUT / name) == val for name, val in manifest.items())
    launch = READ(OUT / "launch.json")
    assert launch["cases"] == [CASE["id"]] and launch["optimizer_updates"] == 0
    assert launch["checkpoint_index_sha256"] == prior.digest(base.MODEL / "model.safetensors.index.json")
    tok = AutoTokenizer.from_pretrained(base.MODEL, local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    branches = [req for req in requests() if req["id"] not in expected["reused"]]
    calls, traces = [prior.wire.n.lines(OUT / name) for name in ("calls.jsonl", "tokens.jsonl")]
    bridges = {}
    for req, row, trace in zip(branches, calls, traces, strict=True):
        res = row["response"]
        assert row["request"] == req and trace["input_ids"] == base.prompt(tok, req)
        assert trace["response"] == res and len(trace["output_ids"]) == res["output_tokens"]
        assert tok.decode(trace["output_ids"], skip_special_tokens=True).strip() == res["text"]
        assert bool(trace["output_ids"] and trace["output_ids"][-1] == eos) == (res["termination"] == "complete")
        bridges[req["id"]] = res | {"elapsed_seconds": row["elapsed_seconds"]}
    old = {r["request"]["id"]: r for r in prior.wire.n.lines(PARENT / "evidence/calls.jsonl")}
    for req in expected["requests"]:
        if req["id"] in expected["reused"]:
            m = req["id"].split("/")[-1]
            source = old[f"bridge-{m}"]
            assert source["request"] | {"id": req["id"]} == req
            bridges[req["id"]] = source["response"] | {"reused": True}
    records, packets = compose(bridges)
    assert len(bridges) == 12 and len(records) == 48
    return {"bridges": bridges, "records": records, "blind_packets": packets, "sha256": manifest}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify"))
    mode = parser.parse_args().mode
    if mode == "run":
        run()
    else:
        frozen.emit({"plan": plan, "verify": verify}[mode]())
