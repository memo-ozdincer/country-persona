"""Test a single UNIFIL public-rubric MARL fit against the frozen transfer."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from unittest.mock import patch

import numpy as np

import unifil_final_review as review

study, route = review.study, review.routing
OUT = study.common.OUT / "unifil-rubric-fit"


def run():
    OUT.mkdir()
    begin = {"pid": os.getpid(), "host": socket.gethostname(), "device": "CPU", "gpu_uuids": [],
             "process_start": subprocess.check_output(["ps", "-o", "lstart=", "-p", str(os.getpid())],
                                                      text=True).strip(),
             "command": [sys.executable, *sys.argv], "run_directory": str(OUT.resolve()),
             "seed": route.SEED, "planned_updates": route.UPDATES,
             "sha256": {p.name: study.common.runner.digest(p) for p in
                        (study.TASK, Path(route.__file__), Path(__file__))}}
    (OUT / "launch.json").write_text(json.dumps(begin, indent=2) + "\n")
    cases = {"public": {"weights": (7, 7, 7), "joint": (3, 14)}}
    assert [r["weight"] for r in study.packet()["rubric"]] == [7] * 10
    with patch.multiple(route, TRAIN_IDS=("public",), TRAIN_PRIORS={"public": route.TEST_PRIORS["uniform"]}):
        *learned, trace = route.train(cases)

    # Only retrospective evaluation accesses any generated records.
    banks = {name: study.OUT / path for name, path in
             (("prose", "score.json"), ("verified", "verified-transport.json"))}
    summary = {}
    for name, path in banks.items():
        input_data = json.loads(path.read_text())
        metrics = {}
        for metric in ("points", "release_points"):
            points = np.array([input_data["bank"][f"team-{i}"][metric] for i in route.STATES])
            if name == "verified":
                assert np.array_equal(points, 35 + route.points(cases["public"]))
            metric_results = {}
            for prior_name, prior in route.TEST_PRIORS.items():
                base = input_data["priors"][prior_name][metric]
                run = route.evaluate(learned, prior, points, route.TRAIN_LOSS)
                erased = route.evaluate(learned, prior, points, route.TRAIN_LOSS, force_missing=True)
                assert run["net"] <= base["exact_optional"]["net"] + 1e-9
                metric_results[prior_name] = {"fit": run, "request_erased": erased,
                                              **{arm: base[arm]["net"] for arm in
                                                 ("exact_independent", "exact_optional", "learned")}}
            metrics[metric] = metric_results
        summary[name] = {"sha256": study.common.runner.digest(path), "metrics": metrics}
    result = {"scope": "Single UNIFIL rubric-only calibration on uniform typed inventories. "
              "The two other priors are excluded from fitting. The pre-existing model records are evaluation banks.",
              "private_reward": route.points(cases["public"]).tolist(), "updates": len(trace),
              "trace": trace, "policy": [p.tolist() for p in learned], "evaluation": summary}
    (OUT / "fit.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    run()
