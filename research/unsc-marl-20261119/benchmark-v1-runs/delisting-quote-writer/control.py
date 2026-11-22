"""Score the fresh CPU control with the same record assembler and routing policies."""
import json
from unittest.mock import patch

import quote_writer as experiment

scoring = experiment.scoring
read = scoring.read
HERE = experiment.HERE


def run():
    spec = experiment.baseline.plan()
    verified = read(HERE / "verified.json")
    control = {key: verified["outputs"][f"control/{key}"] for key in spec["requests"]}
    marks = read(HERE / "control-marks.json")

    def read_for_score(path):
        if path == HERE / "plan.json":
            return spec
        if path == HERE / "verified.json":
            return verified | {"outputs": control}
        if path == HERE / "marks.json":
            return marks
        return read(path)

    with patch.object(scoring, "HERE", HERE), patch.object(scoring, "plan", return_value=spec), patch.object(
        scoring, "read", side_effect=read_for_score
    ):
        return scoring.run()


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
