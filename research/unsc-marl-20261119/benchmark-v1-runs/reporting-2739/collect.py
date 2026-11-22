"""Run the frozen v1.5 actor comparison on the separately locked 2739 case."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
RELEASE = HERE.parents[1] / "benchmark-v1.5"
sys.path.insert(0, str(RELEASE))
sys.path.append(str(HERE.parent / "syria-baseline"))
import run_suite as suite
from importlib.util import module_from_spec, spec_from_file_location

spec = spec_from_file_location("archived_model_collector", HERE.parent / "syria-baseline/collect.py")
base = module_from_spec(spec)
spec.loader.exec_module(base)

e = suite.e
CASE = e.read(HERE / "docket.json")
OUT = HERE / "evidence"


def pin(path):
    return sha256(path.read_bytes()).hexdigest()


def plan():
    suite.verify_release()
    files = (Path(__file__), HERE / "docket.json", HERE / "protocol.md", HERE / "provenance.json",
             HERE / "sources.py", RELEASE / "release.json", Path(base.__file__))
    return {"case": CASE["id"], "arms": list(e.ARMS), "orders": [0, 1], "physical_calls": 16,
            "checkpoint_index_sha256": pin(base.MODEL / "model.safetensors.index.json"),
            "sha256": {str(path.relative_to(HERE.parents[1])): pin(path) for path in files}}


def check_plan():
    assert plan() == e.read(HERE / "plan.json")


def run():
    check_plan()
    with patch.object(base, "roster", return_value={CASE["id"]: CASE}), patch.object(base, "HERE", HERE):
        base.run(OUT)


def lines(file):
    return [json.loads(line) for line in (OUT / file).read_text().splitlines()]


def verify():
    from transformers import AutoTokenizer

    check_plan()
    manifest = e.read(OUT / "complete.json")
    assert set(manifest) == {"actors.jsonl", "episodes.jsonl", "launch.json", "tokens.jsonl"}
    assert all(pin(OUT / name) == digest for name, digest in manifest.items())
    launch = e.read(OUT / "launch.json")
    assert launch["release_sha256"] == pin(RELEASE / "release.json")
    assert launch["collector_sha256"] == pin(Path(base.__file__))
    assert launch["protocol_sha256"] == pin(HERE / "protocol.md")
    assert launch["checkpoint_index_sha256"] == plan()["checkpoint_index_sha256"]
    assert launch["cases"] == [CASE["id"]] and launch["optimizer_updates"] == 0
    tokenizer = AutoTokenizer.from_pretrained(base.MODEL, local_files_only=True)
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    actors, tokens = lines("actors.jsonl"), lines("tokens.jsonl")
    physical = [row for row in actors if not row["reused"]]
    assert len(actors) == 18 and len(physical) == 16
    for row, trace in zip(physical, tokens, strict=True):
        out = row["reply"]
        assert trace["input_ids"] == base.prompt(tokenizer, row["request"])
        assert trace["response"] == out and len(trace["input_ids"]) == out["input_tokens"]
        assert len(trace["output_ids"]) == out["output_tokens"]
        assert tokenizer.decode(trace["output_ids"], skip_special_tokens=True).strip() == out["text"]
        assert bool(trace["output_ids"] and trace["output_ids"][-1] == eos) == (out["termination"] == "complete")
    with patch.object(e, "cases", return_value={CASE["id"]: CASE}):
        _, episodes = suite.report.validate_episodes(lines("episodes.jsonl"))
    packets, traces = {}, {}
    by_request = e.judge.by_id(actors)
    for key, row in episodes.items():
        _, arm, order = key.split("/")
        calls = e.validate_calls(CASE, arm, int(order), row["calls"])
        for i, call in enumerate(calls):
            recorded = by_request[key + f"/{i}"]
            assert e.build_request(CASE, arm, int(order), calls[:i]) == recorded["request"]
            assert all(call[k] == v for k, v in recorded["reply"].items())
            assert recorded["reused"] == (arm == "peer" and i == 0)
        packet = e.judge.request(e.final_packet(CASE, calls))
        packets[packet["id"]] = packet
        traces[key] = {"packet": packet["id"], "turns": calls}
    return {"packets": dict(sorted(packets.items())), "traces": traces, "evidence_sha256": manifest}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("plan", "run", "verify"))
    mode = p.parse_args().mode
    if mode == "run":
        run()
    else:
        e.emit({"plan": plan, "verify": verify}[mode]())
