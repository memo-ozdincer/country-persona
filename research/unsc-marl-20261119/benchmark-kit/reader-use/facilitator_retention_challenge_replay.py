"""Measure how a second gate changes audited record outcomes and cost."""
import argparse
from hashlib import sha256
import json

import facilitator_retention_challenge as study
import facilitator_retention_judge_replay as baseline


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    stage = study.EVIDENCE / "judgments.json"
    fit = study.HERE / "facilitator-measured-channel-evidence/fits.json"
    inputs = baseline.trained.read(stage)
    assert inputs.keys() == study.passed_before().keys()
    assert all(not v["chronology_pass"] or study.passed_before()[k]["chronology_pass"] for k, v in inputs.items())
    _, points, first, alternatives = next(row for row in baseline.pairs.contexts() if row[0] == "2504_chronology")
    result = baseline.replay(points, first, alternatives, inputs, baseline.trained.read(fit), "chronology")
    print(json.dumps({"results": result,
                      "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in (stage, fit)}},
                     ensure_ascii=False, indent=2))
