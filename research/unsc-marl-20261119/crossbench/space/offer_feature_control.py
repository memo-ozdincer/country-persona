"""Isolate observation sharing by fitting raw keys on the same example mixture."""
import json
from pathlib import Path
from unittest.mock import patch

import offer_abstract as experiment

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "evidence/offer-abstract/results.json"


def evaluate():
    reference = json.loads(SOURCE.read_text())
    with patch.object(experiment, "features", side_effect=lambda obs: obs):
        raw = experiment.evaluate()
    return {"scope": "Same train and test rows, objective, baselines and update cap. No observation sharing in the raw arm.",
            "reference_sha256": experiment.offers.sha256(SOURCE.read_bytes()).hexdigest(),
            "raw": raw, "shared_usage": {key: reference[key]["usage"] for key in ("reliable", "missing_returns")}}


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
