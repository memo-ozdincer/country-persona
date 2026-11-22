"""Fit a diagnostic router on actual assembled Mali record scores under one prior."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import source_request_policy as routing
from source_record_run import digest


def fit(path):
    source = json.loads(path.read_text())
    reward = np.array([r["national_points"] for r in source["records"]])
    assert source["trusted_citations"] and source["loss"] == routing.TRAIN_LOSS
    assert [r["mask"] for r in source["records"]] == routing.STATES.tolist()
    fixture = {"weights": reward[routing.BITS[1:]], "joint": (0, 0)}
    assert np.array_equal(routing.points(fixture), reward)
    uniform = routing.TEST_PRIORS["uniform"]
    with patch.multiple(routing, TRAIN_IDS=("mali",), TRAIN_PRIORS={"mali": uniform}):
        *policy, trace = routing.train({"mali": fixture})
    upper = source["exact_optional_typed"]
    arms = {}
    for name, prior in routing.TEST_PRIORS.items():
        row = next(r for r in source["comparisons"] if r["reader"] == "typed" and r["prior"] == name
                   and r["reward"] == "raw_points")
        actual = routing.evaluate(policy, prior, reward + source["fixed_public_points"], source["loss"])
        assert actual["net"] <= upper[name]["net"] + 1e-9
        arms[name] = {"new_fit": actual, "previous_fit": row["arms"]["learned"]["net"],
                      "exact_independent": row["arms"]["exact_independent"]["net"],
                      "exact_optional": upper[name]["net"]}
    return {
        "scope": "Within-docket calibration on uniform typed inputs, with two test priors. All use the same generated record bank.",
        "score_sha256": digest(path),
        "trainer_sha256": digest(Path(routing.__file__)),
        "driver_sha256": digest(Path(__file__)),
        "seed": routing.SEED, "updates": len(trace), "training_reward_by_receipt": reward.tolist(),
        "training_trace": trace, "policy": [part.tolist() for part in policy], "comparison": arms,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("score", type=Path)
    args = parser.parse_args()
    print(json.dumps(fit(args.score), indent=2))
