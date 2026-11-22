"""Generate one historical passage and compose it with the public workshop proof."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import check
import transfer as t

RUN = HERE / "evidence"


def request():
    case, _, _, _ = t.setup()
    return {"max_output_tokens": 185, "messages": [
        {"role": "system", "content": "Write one factual historical paragraph of at most 93 words. Use only the source notes."},
        {"role": "user", "content": json.dumps({"task": (
            "Give the sponsor and draft symbol, adoption date, vote and resolution number. Give the mandate expiry, "
            "readiness for review after six months and island-wide reach. Attribute the parties' unchanged "
            "positions to the Council President and distinguish them from the Council's consensus. Name the Council's settlement framework."
        ), "evidence": [{k: row[k] for k in ("id", "text")} for row in case["sources"]]}, ensure_ascii=False)},
    ]}


def collect(generate, path):
    req = request()
    assert req == t.e.read(HERE / "request.json")
    reply = generate(req)
    t.common.archived.base.suite.append(path / "calls.jsonl", {"request": req, "reply": reply})
    files = (Path(__file__), HERE / "request.json", HERE / "protocol.md", HERE.parent / "case.json",
             HERE.parent / "check.py", t.RUN / "complete.json")
    (path / "inputs.json").write_text(json.dumps(
        {str(p.relative_to(HERE.parent)): sha256(p.read_bytes()).hexdigest() for p in files}, indent=2) + "\n")


def record():
    case, menu, _, _ = t.setup()
    states = [row for row in check.rows("trace.jsonl") if row["stage"] == "writer"]
    state = states[0]["state"]
    one, = [json.loads(line) for line in (RUN / "calls.jsonl").read_text().splitlines()]
    reply = one["reply"]
    historic = reply["text"]
    wording = (
        "Fictional briefing. " + t.common.renderer.public_conditions(case, state) + " "
        + t.proof(case, state) + " This briefing choice does not change the mandate, Council resolution or party positions."
    )
    decision = t.game.terminal(menu, state)[0]
    return {"workshop": wording, "public_decision": decision, "historical": historic,
            "text": f"Decision: {decision}\n\n{wording}\n\n{historic}",
            "termination": reply["termination"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("request", "run", "record"))
    mode = parser.parse_args().mode
    if mode == "request":
        t.e.emit(request())
    elif mode == "record":
        t.e.emit(record())
    else:
        with patch.object(t.common.archived.base.suite, "collect", collect), patch.object(
                t.common.archived.base, "roster", return_value={"history": None}):
            t.common.archived.base.run(RUN)
