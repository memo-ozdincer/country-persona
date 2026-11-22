"""Fit one decentralized router on the same rubric with locally missing proof."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from unittest.mock import patch

import numpy as np

import unifil_inventory_gate as gate

review, study, route = gate.review, gate.study, gate.route
OUT = study.common.OUT / "unifil-admission-fit"


def run():
    OUT.mkdir()
    code = (Path(__file__), Path(route.__file__), Path(gate.__file__), study.TASK)
    record = {"pid": os.getpid(), "host": socket.gethostname(), "device": "CPU", "gpu_uuids": [],
              "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())],
                                                       text=True).strip(),
              "command": [sys.executable, *sys.argv], "run_directory": str(OUT.resolve()),
              "seed": route.SEED, "planned_updates": route.UPDATES,
              "sha256": {p.name: study.common.runner.digest(p) for p in code}}
    (OUT / "launch.json").write_text(json.dumps(record, indent=2) + "\n")
    fixture = {"weights": (7, 7, 7), "joint": (3, 14)}
    unavailable = 7 & ~int(route.BITS[1])
    uniform = route.TEST_PRIORS["uniform"]
    training = {"whole": uniform, "missing_qualifier": gate.project(uniform, unavailable)}
    with patch.multiple(route, TRAIN_IDS=tuple(training), TRAIN_PRIORS=training):
        *fitted, trace = route.train({k: fixture for k in training})
    prev_json = json.loads(review.transport.FIT.read_text())
    previous = study.common.as_policy(prev_json["policy"])
    payload = 35 + route.points(fixture)
    result = {}
    for regime, mask in (("whole", 7), ("missing_qualifier", unavailable)):
        values = payload[route.STATES & mask]
        matrix = route.receipt_matrix(values, route.TRAIN_LOSS)
        result[regime] = {}
        for name, unfiltered in route.TEST_PRIORS.items():
            prior = gate.project(unfiltered, mask)
            independent = route.best_silent(prior, matrix)
            bound, _ = route.exact_optional(prior, matrix, route.TRAIN_LOSS)
            score = route.evaluate(fitted, prior, values, route.TRAIN_LOSS)
            controls = {k: route.evaluate(p, prior, values, route.TRAIN_LOSS) for k, p in
                        (("previous_fit", previous), ("exact_independent", independent),
                         ("exact_optional", bound))}
            assert max(score["net"], controls["previous_fit"]["net"]) <= controls["exact_optional"]["net"] + 1e-9
            result[regime][name] = {
                "revised_fit": score,
                "request_erased": route.evaluate(fitted, prior, values, route.TRAIN_LOSS, force_missing=True),
                **controls,
            }
    report = {"scope": "Case-rubric calibration on an equal mixture of intact and filtered uniform inventories. "
              "Both actors observe only their own admitted proof IDs. No missingness flag, prior label, or "
              "generated language scores enter the fit.",
              "updates": len(trace), "trace": trace, "policy": [p.tolist() for p in fitted],
              "prior_fit_sha256": study.common.runner.digest(review.transport.FIT), "regimes": result}
    (OUT / "fit.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    run()
