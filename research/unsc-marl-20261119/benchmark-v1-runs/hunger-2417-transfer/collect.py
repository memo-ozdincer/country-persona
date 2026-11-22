"""Build, run and verify the locked Resolution 2417 comparison calls."""
import argparse
from itertools import product
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
sys.path.insert(0, str(RUNS / "historical-benchmark-slice"))
import slice_run as engine

OUT = HERE / "evidence"
SYSTEM = (
    "Write only an optional comparison for a factual UN decision record. Compare the "
    "delivered national statement with the delivered clause of the adopted resolution. "
    "Identify each actor and connect both sources only if they support a specific useful "
    "distinction. Keep a delegation's interpretation separate from the Council's action. "
    "Use only the supplied text. If there is no directly supported comparison, return "
    "exactly NONE. Otherwise write one or two sentences and at most 42 words."
)


def requests(case):
    rows = {}
    for order, early, late in product(("canonical", "reversed"), case["delegate"], case["clause"]):
        parts = [("delegation_statement", early["text"]), ("adopted_clause", late["text"])]
        if order == "reversed":
            parts.reverse()
        payload = json.dumps(dict(parts), ensure_ascii=False)
        ident = engine.sha256(payload.encode()).hexdigest()[:16]
        rows[ident] = {
            "order": order, "pair": [early["id"], late["id"]],
            "request": {"max_output_tokens": 120, "messages": [
                {"role": "system", "content": SYSTEM}, {"role": "user", "content": payload}
            ]},
        }
    assert len(rows) == 12
    return dict(sorted(rows.items()))


def plan():
    assert engine.run_suite.verify_release() == "1.7"
    inputs = (Path(__file__), HERE/"protocol.md", HERE/"case.json", HERE/"provenance.json",
              HERE/"provenance.py", Path(engine.__file__), engine.RELEASE/"release.json",
              RUNS/"terminal-feedback-routing/fit.py", RUNS/"terminal-feedback-routing/plan.json")
    return {
        "inputs_sha256": {str(p.relative_to(RUNS.parent)): engine.run_suite.pin(p) for p in inputs},
        "checkpoint": str(engine.MODEL),
        "checkpoint_index_sha256": engine.run_suite.pin(engine.MODEL/"model.safetensors.index.json"),
        "requests": requests(engine.e.read(HERE/"case.json")),
        "training": {"episodes_per_arm": 1024, "checkpoints": [64, 256, 1024]},
    }


def run(spec):
    def collect(call, out):
        for key, row in spec["requests"].items():
            reply = call(row["request"])
            engine.run_suite.append(out/"actors.jsonl", {"id": key, "reply": reply})
            engine.run_suite.append(out/"episodes.jsonl", {"id": key, "pair": row["pair"], "order": row["order"]})
    with patch.object(engine, "HERE", HERE), patch.object(engine, "OUT", OUT), patch.object(
        engine.run_suite, "collect", side_effect=collect
    ):
        engine.run()


def verify(spec):
    from transformers import AutoTokenizer

    hashes = engine.e.read(OUT/"complete.json")
    assert all(engine.run_suite.pin(OUT/name) == pin for name, pin in hashes.items())
    tok = AutoTokenizer.from_pretrained(engine.MODEL, local_files_only=True)
    eos = tok.convert_tokens_to_ids("<|im_end|>")
    actor, tokens, episodes = (engine.report.load(OUT/file) for file in
                              ("actors.jsonl", "tokens.jsonl", "episodes.jsonl"))
    result = {}
    for (key, row), output, trace, episode in zip(spec["requests"].items(), actor, tokens, episodes, strict=True):
        assert output["id"] == episode["id"] == key
        assert episode == {"id": key, "order": row["order"], "pair": row["pair"]}
        assert trace["request"] == row["request"]
        assert trace["input_ids"] == engine.get_tokens(tok, row["request"])
        ids = trace["output_ids"]
        reply = output["reply"]
        assert reply["input_tokens"] == len(trace["input_ids"])
        assert reply["output_tokens"] == len(ids) <= row["request"]["max_output_tokens"]
        assert reply["text"] == tok.decode(ids, skip_special_tokens=True).strip()
        assert (reply["termination"] == "complete") == bool(ids and ids[-1] == eos)
        result[key] = reply
    return {"hashes": hashes, "outputs": result}


def review_packets(spec):
    case = engine.e.read(HERE/"case.json")
    cards = {block["id"]: block for block in case["delegate"]+case["clause"]}
    outputs = engine.e.read(HERE/"verification.json")["outputs"]
    for key, row in spec["requests"].items():
        sources = [cards[name] for name in row["pair"]]
        sources.sort(key=lambda source: source["id"])
        yield {"id": key, "sources": sources, "comparison": outputs[key]["text"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify", "packets"))
    args = parser.parse_args()
    spec = plan()
    if args.mode != "plan":
        assert spec == engine.e.read(HERE/"plan.json")
    if args.mode == "run":
        run(spec)
    else:
        engine.e.emit({"plan": lambda: spec, "verify": lambda: verify(spec),
                       "packets": lambda: list(review_packets(spec))}[args.mode]())


if __name__ == "__main__":
    main()
