"""Test a source-quoted comparison writer on the frozen 2744 receipt bank."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import re
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "delisting-comparison-writer"
sys.path.insert(0, str(PRIOR))
import collect_relation as baseline
import score as scoring

SYSTEM = (
    baseline.SYSTEM
    + ' In a supported comparison embed one short exact phrase from each source in double quotes. '
    'Choose phrases that carry the actor, action, timing or legal force. Copy the operative verb '
    'exactly when its force matters. Attribute each quote to its own source and state their '
    'specific relationship. Count the quoted words toward the same 40-word limit.'
)


def plan():
    spec = deepcopy(baseline.plan())
    assert spec == baseline.read(PRIOR / "plan.json")
    control = deepcopy(spec["requests"])
    for request in spec["requests"].values():
        request["messages"][0]["content"] = SYSTEM
    spec["requests"].update({f"control/{key}": row | {"id": f"control/{key}"} for key, row in control.items()})
    for path in (Path(__file__), HERE / "protocol.md", PRIOR / "plan.json", PRIOR / "score.py"):
        spec["pins"][str(path.relative_to(HERE.parents[1]))] = baseline.pin(path)
    return spec


def main(mode):
    spec = plan()
    if mode == "plan":
        return spec
    assert spec == baseline.read(HERE / "plan.json")
    if mode == "score":
        verified = baseline.read(HERE / "verified.json")
        archived = baseline.read(PRIOR / "verified.json")["outputs"]
        control = {key: verified["outputs"][f"control/{key}"] for key in archived}
        quote_spec = spec | {"requests": {key: spec["requests"][key] for key in archived}}
        outputs = {key: verified["outputs"][key] for key in archived}

        def read_for_score(path):
            if path == HERE / "plan.json":
                return quote_spec
            if path == HERE / "verified.json":
                return verified | {"outputs": outputs}
            return baseline.read(path)

        with patch.object(scoring, "HERE", HERE), patch.object(scoring, "plan", return_value=quote_spec), patch.object(
            scoring, "read", side_effect=read_for_score
        ):
            result = scoring.run()
        quote_checks = {}
        for key, reply in outputs.items():
            sources = json.loads(quote_spec["requests"][key]["messages"][1]["content"])
            quotes = re.findall(r'"([^"]+)"|“([^”]+)”', reply["text"])
            quote_checks[key] = [
                {"quote": left or right, "sources": [k for k, text in sources.items() if (left or right) in text]}
                for left, right in quotes
            ]
        return result | {"quote_checks": quote_checks, "control_matches_archived": {
            key: reply == archived[key] for key, reply in control.items()
        }}
    with patch.object(baseline.chair, "HERE", HERE), patch.object(
        baseline.chair, "OUT", HERE / "evidence"
    ), patch.object(baseline.chair, "BUDGET", baseline.BUDGET), patch.object(
        baseline.chair, "locked", return_value=spec
    ):
        return {"run": baseline.chair.run, "verify": baseline.chair.verify}[mode]()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify", "score"))
    mode = parser.parse_args().mode
    result = main(mode)
    if mode != "run":
        print(json.dumps(result, ensure_ascii=False, indent=2))
