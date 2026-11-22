"""Reload both learned policies and replay their exact four-option evaluations."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

import torch

from learn import Actor, HERE, ROOT, SEED, TEST_OPTIONS, UPDATES, exact, run, summarize


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit():
    worlds = exact(TEST_OPTIONS)
    torch.set_num_threads(1)
    torch.manual_seed(SEED)
    model = Actor()
    before = {k: v.detach().clone() for k, v in model.state_dict().items()}
    initial = run(model, worlds, "peer")[0]
    result = {}
    after = {}
    for name in ("terminal", "dense"):
        p = HERE / name
        launch = read(p / "launch.json")
        locks = [HERE / "learn.py", HERE / "protocol.py", ROOT / "decision_ledger.py"]
        if name == "terminal":
            locks.append(HERE / "capacity.json")
        else:
            locks.extend((HERE / "learn_dense.py", HERE / "terminal" / "launch.json", HERE / "terminal" / "results.json"))
        for path in locks:
            assert digest(path) == launch["hashes"][path.name]
        assert launch["seed"] == SEED and launch["updates"] == UPDATES
        log = [json.loads(line) for line in (p / "updates.jsonl").read_text().splitlines()]
        assert [r["step"] for r in log] == list(range(1, UPDATES + 1))
        assert all(math.isfinite(r["grad_norm"]) and math.isfinite(r["loss"]) for r in log)
        metrics = read(p / "results.json")
        assert metrics["initial"] == read(p / "initial.json") == summarize(initial)
        traces = read(p / "traces.json")
        if "initial" in traces:
            assert traces["initial"] == initial
        model.load_state_dict({k: torch.tensor(v) for k, v in read(p / "state.json").items()})
        actual = {}
        with torch.no_grad():
            for mode in ("peer", "silent"):
                rows = run(model, worlds, mode)[0]
                assert rows == traces[mode] and summarize(rows) == metrics[mode]
                actual[mode] = rows
        result[name] = {
            "finite_updates": len(log),
            "nonzero_gradient_updates": sum(r["grad_norm"] > 0 for r in log),
            "changed_parameter_tensors": [k for k, v in model.state_dict().items() if not torch.equal(before[k], v)],
            "training_initial_10_impasses": sum(r["impasse"] for r in log[:10]),
            "training_final_10_impasses": sum(r["impasse"] for r in log[-10:]),
            "metrics": {k: metrics[k] for k in ("initial", "peer", "silent")},
        }
        after[name] = actual
    effects = Counter((a["feasible"], a["state"] != "UNRESOLVED", b["state"] != "UNRESOLVED")
                      for a,b in zip(after["terminal"]["peer"], after["dense"]["peer"]))
    return {"profiles_per_arm": len(worlds), "training_runs": result,
            "paired_feasible_terminal_dense": {str(k): n for k, n in effects.items()}}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
