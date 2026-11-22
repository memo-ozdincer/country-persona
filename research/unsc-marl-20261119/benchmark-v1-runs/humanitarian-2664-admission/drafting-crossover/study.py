"""Collection and exact prompt/token replay for the Resolution 2664 crossover."""
import argparse
from importlib.util import module_from_spec, spec_from_file_location
import json
import os
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
RUNS = HERE.parents[1]
RELEASE = RUNS.parent / "benchmark-v1.5"
CASE = json.loads((HERE.parent / "case.json").read_text())
EVIDENCE = {row["id"]: row["text"] for row in CASE["evidence"]}
DESKS = ("safeguards", "india")
ARMS = ("independent", "peer", "solo")
OUT = HERE / "evidence"
NOTE = (
    "Write one working note for the final Council briefing. Focus on your assigned subject. "
    "Use only the supplied evidence and any earlier note. Preserve precise actors, "
    "dates, scope, and qualifications. Connect earlier information to your own points "
    "where it helps explain the record. Keep the note below 65 words and end there."
)
FINAL = (
    CASE["task"] + " You have two public evidence cards and two working notes. "
    "Use the notes as source summaries. Preserve any supplied time limits and distinguish "
    "the Council's actions from assessments made by a national delegation. Return just the brief."
)


def load_module(name, path):
    spec = spec_from_file_location(name, path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


collector = load_module("collector_2664", RUNS / "syria-baseline/collect.py")


def read(path):
    return json.loads(path.read_text())


def plan():
    paths = [Path(__file__), HERE / "protocol.md", HERE.parent / "case.json",
             HERE.parent / "anchors.json", RELEASE / "release.json", Path(collector.__file__)]
    return {
        "pins": {str(path.relative_to(RUNS.parent)): collector.sha(path) for path in paths},
        "checkpoint_index_sha256": collector.sha(collector.MODEL / "model.safetensors.index.json"),
        "note_cap": 108, "final_cap": 220, "physical_calls": 14,
    }


def request(key, cap, system, payload):
    return {"id": key, "max_output_tokens": cap, "messages": [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]}


def note(generate, key, desk, pooled=False, preceding=None):
    cards = DESKS if pooled else (desk,)
    payload = {"assigned_subject": desk, "evidence": {card: EVIDENCE[card] for card in cards}}
    if preceding is not None:
        payload["earlier_note"] = preceding
    return generate(request(key, 108, NOTE, payload))


def episode(generate):
    local = {desk: note(generate, f"local/{desk}", desk) for desk in DESKS}
    result = {}
    for first in DESKS:
        second = DESKS[1 - DESKS.index(first)]
        peer = note(generate, f"peer/{first}/second", second, preceding=local[first]["text"])
        solo_first = note(generate, f"solo/{first}/first", first, pooled=True)
        solo_second = note(generate, f"solo/{first}/second", second, pooled=True, preceding=solo_first["text"])
        paths = {"independent": (local[first], local[second]), "peer": (local[first], peer),
                 "solo": (solo_first, solo_second)}
        for arm in ARMS:
            notes = paths[arm]
            key = f"{arm}/{first}/final"
            payload = {"public": {card: EVIDENCE[card] for card in ("vote", "scope")},
                       "notes": [reply["text"] for reply in notes]}
            final = generate(request(key, 220, FINAL, payload))
            result[key] = {"notes": list(notes), "final": final,
                           "input_tokens": sum(r["input_tokens"] for r in (*notes, final)),
                           "output_tokens": sum(r["output_tokens"] for r in (*notes, final))}
    return result


def collect(generate, directory):
    def call(spec):
        response = generate(spec)
        collector.suite.append(directory / "calls.jsonl", {"request": spec, "reply": response})
        return response
    (directory / "briefs.json").write_text(json.dumps(episode(call), ensure_ascii=False, indent=2) + "\n")


def run():
    assert plan() == read(HERE / "plan.json")
    assert os.environ.get("CUDA_VISIBLE_DEVICES", "").startswith("GPU-")
    with patch.object(collector, "roster", return_value={"humanitarian-2664": CASE}), patch.object(
        collector, "HERE", HERE), patch.object(collector.suite.e, "HERE", RELEASE), patch.object(
        collector.suite, "collect", collect
    ):
        collector.run(OUT)


def verify():
    from transformers import AutoTokenizer

    locked = plan()
    assert locked == read(HERE / "plan.json")
    manifest = read(OUT / "complete.json")
    assert set(manifest) == {"briefs.json", "calls.jsonl", "launch.json", "tokens.jsonl"}
    assert all(collector.sha(OUT / name) == digest for name, digest in manifest.items())
    launch = read(OUT / "launch.json")
    assert launch["checkpoint_index_sha256"] == locked["checkpoint_index_sha256"]
    assert launch["gpu_name"] == "NVIDIA RTX PRO 6000 Blackwell Server Edition"
    assert launch["optimizer_updates"] == 0 and launch["release_sha256"] == collector.sha(RELEASE / "release.json")
    tokenizer = AutoTokenizer.from_pretrained(collector.MODEL, local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    calls, traces = ([json.loads(line) for line in (OUT / name).read_text().splitlines()]
                     for name in ("calls.jsonl", "tokens.jsonl"))
    assert len(calls) == len(traces) == locked["physical_calls"]
    pairs = iter(zip(calls, traces, strict=True))

    def call(spec):
        saved, trace = next(pairs)
        assert spec == saved["request"] and trace["response"] == saved["reply"]
        assert trace["input_ids"] == collector.prompt(tokenizer, spec)
        reply = saved["reply"]
        ids = trace["output_ids"]
        assert len(trace["input_ids"]) == reply["input_tokens"]
        assert 0 < len(ids) == reply["output_tokens"] <= spec["max_output_tokens"]
        assert tokenizer.decode(ids, skip_special_tokens=True).strip() == reply["text"]
        assert eos not in ids[:-1] and (ids[-1] == eos) == (reply["termination"] == "complete")
        return reply

    result = episode(call)
    assert result == read(OUT / "briefs.json") and next(pairs, None) is None
    return {"calls": len(calls), "finals": len(result), "briefs": result, "manifest": manifest}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("run", "verify", "plan"))
    mode = parser.parse_args().mode
    if mode == "run":
        run()
    else:
        print(json.dumps({"plan": plan, "verify": verify}[mode](), ensure_ascii=False, indent=2))
