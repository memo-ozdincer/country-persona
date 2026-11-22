"""Fit the same decentralized router on Myanmar's public rubric, without model-written rewards."""
import argparse
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from unittest.mock import patch

import numpy as np

import myanmar_protected_writer as writer
import source_request_policy as routing
from source_record_run import digest


def run(score_path, output):
    output.mkdir()
    launch = {"host": socket.gethostname(), "pid": os.getpid(), "device": "CPU", "gpu_uuids": [],
              "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())],
                                                       text=True).strip(),
              "command": [sys.executable, *sys.argv], "run_directory": str(output.resolve()),
              "seed": routing.SEED, "optimizer_updates_planned": routing.UPDATES,
              "rubric_sha256": digest(writer.TASK), "trainer_sha256": digest(Path(routing.__file__)),
              "driver_sha256": digest(Path(__file__)), "evaluation_sha256": digest(score_path)}
    (output / "launch.json").write_text(json.dumps(launch, indent=2) + "\n")
    weights = {r["id"]: r["weight"] for r in writer.packet()["rubric"]}
    expected_fixture = {"weights": [weights[unit] for unit in ("uk", "india", "role")],
                        "joint": (writer.RECEIPT_UNITS["overlap"][0], weights["overlap"])}
    prior = routing.TEST_PRIORS["uniform"]
    expected = routing.points(expected_fixture)
    with patch.multiple(routing, TRAIN_IDS=("public-rubric",), TRAIN_PRIORS={"public-rubric": prior}):
        *policy, trace = routing.train({"public-rubric": expected_fixture})
    plan, count = routing.exact_optional(prior, routing.receipt_matrix(expected, routing.TRAIN_LOSS),
                                         routing.TRAIN_LOSS)

    # The actual generations are accessed only after learning and planning.
    archive = json.loads(score_path.read_text())
    assert archive["loss"] == routing.TRAIN_LOSS and digest(score_path) == launch["evaluation_sha256"]
    assert tuple(archive["field_order"]) == tuple(writer.FIELDS)
    actual = np.array([r["points"] for r in archive["records"]])
    results = {}
    for name, test in routing.TEST_PRIORS.items():
        loss = archive["loss"]
        old = archive["priors"][name]
        results[name] = {
            "learned_rubric": routing.evaluate(policy, test, actual, loss),
            "learned_request_erased": routing.evaluate(policy, test, actual, loss, force_missing=True),
            "exact_public_rubric": routing.evaluate(plan, test, actual, loss),
            "exact_independent_actual": old["exact_independent"]["net"],
            "exact_optional_actual": old["exact_optional"]["net"],
        }
    receipt = {"scope": "Myanmar task-aware adaptation. Training and planning use the published rubric and uniform prior, "
                        "before opening the already-generated model record bank for scoring. The public rubric assumes "
                        "the writer satisfies the required claims for any delivered sources.",
               "expected_national_points_by_receipt": expected.tolist(),
               "actual_points_by_receipt": actual.tolist(), "updates": len(trace), "trace": trace,
               "learned_policy": [p.tolist() for p in policy], "exact_planner_policy": [p.tolist() for p in plan],
               "planner_maps_examined": count, "actual_results": results}
    (output / "fit.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("score", type=Path)
    cli.add_argument("output", type=Path)
    args = cli.parse_args()
    run(args.score, args.output)
