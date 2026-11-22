"""Test whether a weak initial reference bias permits a distinct opening policy."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_passage_joint_fit as study

fit, R = study.fit, study.R
START = (0., 0., 1., -.1)


def run():
    archive = study.historic.read(study.EVIDENCE / "results.json")
    fixed = archive["training"]["fixed_opening"]
    fitting = fit.OLD.base.cases()[0]
    with patch.object(study, "OPEN_INITIAL", START):
        learned = study.train(fitting, learn_opening=True)
    initial = {"opening_learned": True, "weights": [START, START, *fit.OLD.INITIAL]}
    evidence = {}
    for event, (points, channel) in study.held().items():
        cases = {}
        for label in fit.live.PRIORS:
            prior = R.TEST_PRIORS[label]
            outcome = study.evaluate(points, channel, prior, {"joint": learned, "fixed_opening": fixed})
            pure, soft = study.policies(points, prior, initial)
            start = study.metric(pure, prior, points, channel)
            start["team"] = [a.tolist() for a in pure]
            start["stochastic_net"] = study.soft_net(soft, prior, points, channel)
            outcome["initial_policy"] = start
            cases[label] = outcome
        evidence[event] = cases
    files = (Path(__file__).resolve(), Path(study.__file__).resolve(), study.EVIDENCE / "weak-start-protocol.md",
             study.EVIDENCE / "results.json")
    return {"initial_opening_weights": START, "fit": learned, "cases": evidence,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(run(), ensure_ascii=False, indent=2))
