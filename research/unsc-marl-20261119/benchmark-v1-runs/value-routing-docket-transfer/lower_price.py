"""Evaluate the frozen transfer policies when partial reports can pay for themselves."""
from hashlib import sha256
import json
from pathlib import Path
import runpy
from unittest.mock import patch

import numpy as np

WORK = Path(__file__).resolve().parent
PRICES = (1, 3, 5)


def run():
    ns = runpy.run_path(str(WORK / "fit.py"))
    source = ns["read"](WORK / "plan.json")
    results = ns["read"](WORK / "results.json")
    outputs = ns["read"](WORK / "verified.json")["outputs"]
    cases = source["cases"]
    bank = ns["bank"](cases, outputs)[1]
    learner, team = ns["learner"], ns["team"]
    weights = []
    for group in ("value_history", "sampled_history"):
        weights.append(tuple(np.array(results[group][-1][name]) for name in ("sender", "receiver")))
    assert not set(PRICES) & (set(team.TRAIN_PRICES) | set(team.TEST_PRICES))
    with patch.object(team, "PRIVATE", {k: tuple(v["early"]) for k, v in cases.items()}), patch.object(
            team, "TEST_PRICES", PRICES):
        summary = learner.fit.compare(bank, *weights)
    return {"prices": list(PRICES), "fit_sha256": sha256((WORK / "results.json").read_bytes()).hexdigest(),
            "results": summary}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
