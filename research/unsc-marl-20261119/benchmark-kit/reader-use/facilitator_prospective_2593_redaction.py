"""Replay question-blind writing while preserving the exact same request and route."""
import argparse
import json
from pathlib import Path

import numpy as np

import facilitator_prospective_2593 as study


def replay(directory):
    rows = study.verify(directory)
    review = json.loads((study.EVIDENCE / "review.json").read_text())
    actual = study.score(rows, review)
    decoded = actual["decoded"]
    approved = set(actual["approved_reply_ids"])
    # A writer sees only the selected card. The decoder and the chooser retain
    # the original question, local constraints and every communication cost.
    blind = np.broadcast_to([f"reply/0/{card}" in approved for card in range(4)], (4, 4))
    result = {}
    for label in study.PRIORS:
        prior = study.ROUTE.TEST_PRIORS[label]
        result[label] = {}
        for arm, policy in study.policies(prior).items():
            clean = study.distribution(policy, prior, decoded, blind)
            observed = actual["priors"][label][arm]
            fields = ("guarded_points", "strict_complete", "net", "cost", "attempts")
            assert abs(clean["cost"] - observed["english"]["cost"]) < 1e-12
            assert abs(clean["attempts"] - observed["english"]["attempts"]) < 1e-12
            result[label][arm] = {"question_blind": {k: clean[k] for k in fields},
                                  "delta_from_visible": {k: clean[k] - observed["english"][k] for k in fields},
                                  "max_receipt_mass_delta_from_typed": max(abs(a - b) for a, b in
                                      zip(clean["mass"], observed["typed"]["mass"], strict=True))}
    return result


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    print(json.dumps(replay(cli.parse_args().directory), indent=2))
