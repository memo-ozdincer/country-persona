"""Accept exact quotes using the desk and source identity at the transport boundary."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import review_witness_run as review

m, e = review.m, review.e
RUN = HERE / "evidence"
CAP = 2


def admit(reply, request):
    generated = m.h.r.parse(reply)
    expected = json.loads(request["messages"][-1]["content"])
    return set(generated) == {"card", "quote"} and generated["quote"] == expected["evidence"]


def execute(generate):
    context, inventory, _ = m.select()
    source = {e.checksum(row["request"]): row["reply"] for row in review.read_lines("calls.jsonl")}
    original_asks = []
    novel = []
    def ask(request):
        key = e.checksum(request)
        if key in source:
            original_asks.append(key)
            return source[key]
        if len(novel) >= CAP:
            raise ValueError("Native cap reached before a new follow-up")
        novel.append(request)
        return generate(request)

    with patch.object(m, "validate", admit):
        result = list(m.simulate(context, inventory, ask))
    return result, original_asks, novel


def plan():
    streams, old, new = execute(m.ideal)
    assert new
    return {"old_prompt_hashes": old, "new_requests": new,
            "expected_masks": {path["arm"]: path["final_mask"] for path in streams}}


def pins():
    files = (Path(__file__), HERE / "protocol.md", HERE / "plan.json", HERE.parent / "live.py",
             m.RUN / "calls.jsonl", m.RUN / "complete.json", m.RUN / "trace.jsonl")
    return {str(path.relative_to(HERE.parent)): sha256(path.read_bytes()).hexdigest() for path in files}


def collect(generate, path):
    assert plan() == e.read(HERE / "plan.json")

    def log(request):
        result = generate(request)
        m.h.r.w.archived.base.suite.append(path / "calls.jsonl", {"request": request, "reply": result})
        return result

    rows, saved, new = execute(log)
    for row in rows:
        m.h.r.w.archived.base.suite.append(path / "trace.jsonl", row)
    (path / "inputs.json").write_text(json.dumps(pins(), indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run"))
    if parser.parse_args().mode == "plan":
        e.emit(plan())
    else:
        with patch.object(m.h.r.w.archived.base.suite, "collect", collect), patch.object(
                m.h.r.w.archived.base, "roster", return_value={"scoped": None}):
            m.h.r.w.archived.base.run(RUN)
