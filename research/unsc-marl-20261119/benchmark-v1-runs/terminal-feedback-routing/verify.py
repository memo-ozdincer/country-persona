"""Audit receipt credit and exact policy bounds independently of the fitter."""
from collections import Counter
from itertools import product
import json
import runpy
from pathlib import Path
from types import SimpleNamespace

import numpy as np

fit = SimpleNamespace(**runpy.run_path(str(Path(__file__).with_name("fit.py"))))


def verify():
    result = json.loads((fit.HERE / "results.json").read_text())
    data, _ = fit.prior.environment()
    compact = result["reward_tables"]["compact_ungated"]
    prior = json.loads((fit.DONOR / "results.json").read_text())
    reference = prior["evaluation"]["compact_ungated"]["summary"]
    checks = 0
    for arm, trace in result["fits"].items():
        counts = Counter()
        for step, batch in enumerate(trace["training"], 1):
            for key, score in zip(batch["indices"], batch["scores"], strict=True):
                assert score == compact[key]
                counts[key] += 1
                checks += 1
            checkpoint = trace["checkpoints"].get(str(step * fit.BATCH))
            if checkpoint:
                assert checkpoint["counts"] == [counts[k] for k in range(12)]
                if arm.startswith("receipt_value/"):
                    assert checkpoint["estimate"] == [value if counts[k] else 35
                                                        for k, value in enumerate(compact)]
    assert checks == 4 * max(fit.OBSERVATIONS)

    held = result["evaluation"]["256"]["compact_ungated"]
    assert held["summary"]["oracle/peer"]["utility"] == reference["oracle"]["utility"]
    assert held["summary"]["oracle/independent"]["utility"] == reference["best_arrival"]["utility"]
    policy_checks = 0
    for row in held["rows"]:
        q0, q1, cost, mass = row["setting"]
        for arm, peer in fit.CONTENT.items():
            observed = fit.view_observations(data, peer)
            candidates = []
            for sender in product((0, 1), repeat=3):
                for reply in product((0, 1), repeat=int(observed.max()) + 1):
                    value = 0.
                    for view, front, back in product(range(3), (False, True), (False, True)):
                        mass0 = (q0 if front else 1 - q0) if sender[view] else int(not front)
                        mass1 = q1 if back else 1 - q1
                        doc = reply[observed[view]] if front else reply[0]
                        key = 6 + 2 * view + doc if front and back else (
                            1 + view if front else (4 + doc if back else 0))
                        value += mass[view] * mass0 * mass1 * (compact[key] - cost * sender[view])
                    candidates.append(round(value, 8))
            assert max(candidates) == row["arms"][f"oracle/{arm}"][0]
            assert row["arms"][f"receipt_value/{arm}"][0] == max(candidates)
            policy_checks += 1
    return {"terminal_observations_checked": checks, "held_arm_optima_replayed": policy_checks,
            "same_archived_oracle_means": True}


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2))
