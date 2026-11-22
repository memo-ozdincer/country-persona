"""Connect the query-necessity witness to live passage transport and scoring."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import live_somalia as w
import grade_live as g

n, e, r, t, o, a, D = w.n, w.e, w.r, w.t, w.o, w.a, w.D
OUT = HERE / "evidence"
WITNESS = HERE.parent / "query-witnesses.json"


def settings():
    witness = n.read(WITNESS)["first"][0]
    docket = n.read(t.SOURCE)
    numeric = t.HERE / "numeric-results.json"
    bank = np.array(n.read(numeric)["score_banks"]["native"])
    law, _ = a.laws()[witness["prior"]]
    initializer = n.read(o.replan.study.OLD)["training"]["budget_fit"]
    openings = o.replan.study.opening(r.f.views(bank)["4"], law, initializer)
    mass = o.opening(*openings, law)
    calibration = {i: bank[i] for i in range(7) if i != 3}
    decisions = r.evaluate_locked(calibration, bank[3], law, openings, mass, {})
    team = decisions["interval_team"][1]
    fixed = decisions["interval_fixed"][1]
    arms = {"interval_team": team, "query_erased": team, "interval_fixed": fixed,
            "fixed_us": (np.where(D.CHAIR_LEGAL[:, 3], 3, 0), team[1])}
    return docket, docket["roles"], tuple(witness["world"]), tuple(witness["delivery"]), openings, arms


def plan():
    deck = t.HERE / "numeric-grades.json"
    selection = n.read(deck)["selection"]
    requests = []

    def generate(request):
        requests.append(request)
        owner = json.loads(request["messages"][-1]["content"])["speaker"]
        return {"text": json.dumps(selection[owner][0]), "termination": "complete"}

    output = w.simulate(generate)
    receipts = {name: v["receipt"] for name, v in output["arms"].items()}
    assert receipts["interval_team"] != receipts["query_erased"]
    assert output["physical_calls"] == len(requests) <= w.LIMIT
    files = (Path(__file__), HERE / "protocol.md", WITNESS, Path(w.__file__), t.SOURCE, deck)
    return {"requests": requests, "expected_receipts": receipts,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in files}}


def collect(generate, folder):
    assert plan() == n.read(HERE / "plan.json")

    def trace(request):
        reply = generate(request)
        n.base.suite.append(folder / "calls.jsonl", {"request": request, "response": reply})
        return reply

    output = w.simulate(trace)
    (folder / "dispatch.json").write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify", "score"))
    mode = parser.parse_args().mode
    with patch.multiple(w, settings=settings, OUT=OUT, HERE=HERE, plan=plan), patch.object(g, "HERE", HERE):
        if mode == "run":
            with patch.object(n.base.suite, "collect", collect), patch.object(
                    n.base, "roster", return_value={"matched-somalia-query-necessity": None}):
                n.base.run(OUT)
        else:
            e.emit({"plan": plan, "verify": w.verify, "score": g.run}[mode]())
