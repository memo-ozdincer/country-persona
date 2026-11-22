"""Re-encode an addressed source with its material qualifier attached."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent))
import causal_live as c
import audit_live as audit

w, e, n, g, t = c.w, c.e, c.n, c.g, c.t
OUT = HERE / "evidence"
OLD = c.OUT
EXPANSION = {"73": ["7", "3"], "5": ["5"]}


def load():
    old = n.lines(OLD / "calls.jsonl")
    target = [row for row in old if target_prompt(row["request"])]
    assert len(target) == 1 and json.loads(target[0]["response"]["text"]) in ([7], ["7"])
    return {e.checksum(row["request"]): row["response"] for row in old}, target[0]["request"]


def target_prompt(request):
    data = json.loads(request["messages"][-1]["content"])
    return (data["speaker"], data["stage"], data["heard_question"]) == ("us", "reply", "us")


def new_request(original):
    payload = json.loads(original["messages"][-1]["content"])
    role_menu = payload["passages"]
    payload["passages"] = {"73": role_menu["7"] + " " + role_menu["3"], "5": role_menu["5"]}
    return t.LIB.b.request("Select complete passages that preserve the U.S. vote, reason and reporting reservation. "
                           "Return a JSON array of ID strings. Omit secondary details.", payload, 72)


def plan():
    _, prompt = load()
    files = (Path(__file__), HERE / "protocol.md", OLD / "complete.json", c.WITNESS, t.SOURCE)
    return {"request": new_request(prompt), "expansion": EXPANSION,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in files}}


def expanded(response):
    selected, status = w.wire.normalize({"part": "us", "response": response}, {"us": EXPANSION})
    ids = [item for group in selected for item in EXPANSION[group]]
    return response | {"text": json.dumps(ids), "wire_status": status}


def simulate(actual):
    saved, original = load()
    learned = expanded(actual)

    def use(request):
        key = e.checksum(request)
        return learned if request == original else saved[key]

    with patch.object(w, "settings", c.settings):
        return w.simulate(use) | {"fresh": 1, "reused_original": len(saved) - 1,
                                  "compound_response": actual, "expanded_passages": json.loads(learned["text"])}


def collect(generate, folder):
    assert plan() == n.read(HERE / "plan.json")
    request = plan()["request"]
    reply = generate(request)
    n.base.suite.append(folder / "calls.jsonl", {"request": request, "response": reply})
    (folder / "dispatch.json").write_text(json.dumps(simulate(reply), indent=2, ensure_ascii=False) + "\n")


def verify():
    token_audit = t.LIB.audit
    path = OUT / "complete.json"
    snap = n.read(path)
    assert set(snap) == {"calls.jsonl", "tokens.jsonl", "launch.json", "dispatch.json"}
    assert all(sha256((OUT / key).read_bytes()).hexdigest() == value for key, value in snap.items())
    disk_read = n.read

    def view(file):
        if file == path:
            return {k: v for k, v in snap.items() if k != "dispatch.json"}
        return disk_read(file)

    def calls():
        rows = n.lines(OUT / "calls.jsonl")
        assert len(rows) == 1 and rows[0]["request"] == plan()["request"]
        return rows

    with patch.object(n, "OUT", OUT), patch.object(n, "read", view), patch.object(token_audit, "calls", calls):
        verdict = token_audit.verify()
    assert json.loads(json.dumps(simulate(calls()[0]["response"]))) == n.read(OUT / "dispatch.json")
    return verdict | {"dispatch_replayed": True, "dispatch_sha256": snap["dispatch.json"]}


def score():
    with patch.object(w, "OUT", OUT), patch.object(g, "HERE", HERE):
        return g.run()


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("plan", "run", "verify", "score"))
    mode = cli.parse_args().mode
    if mode == "run":
        with patch.object(n.base.suite, "collect", collect), patch.object(
                n.base, "roster", return_value={"somalia-live-atomic-position": None}):
            n.base.run(OUT)
    else:
        e.emit({"plan": plan, "verify": verify, "score": score}[mode]())
