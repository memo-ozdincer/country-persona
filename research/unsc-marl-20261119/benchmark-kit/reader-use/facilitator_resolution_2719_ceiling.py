"""Check authored evidence ceilings and replay frozen requesters on them."""
import argparse
from hashlib import sha256
import json

import numpy as np

import facilitator_baseline_request_fit as policy
import facilitator_resolution_2719_score as score

study = score.study


def run():
    spec = study.packet()
    values = score.ceilings(spec["criteria"])
    banks = policy.archive.banks()
    training = policy.fit.OLD.base.cases()[0]
    known = {**training, **banks}
    assert all(values != public.tolist() and values != target.tolist() for public, target in known.values())
    observed = np.array(values)
    edges = [{"before": m, "after": m | b, "ceiling_change": int(observed[m | b] - observed[m])}
             for m in range(8) for b in (1, 2, 4) if not m & b]
    assert len(edges) == 12 and min(e["ceiling_change"] for e in edges) > 0
    archive = policy.EVIDENCE / "results.json"
    fitted = json.loads(archive.read_text())["fitted"]
    robust = json.loads(policy.WEIGHTS.read_text())["robust"]
    cases = {}
    for label in policy.fit.live.PRIORS:
        prior = policy.R.TEST_PRIORS[label]
        cases[label] = {name: policy.evaluate(observed, observed, prior, robust, np.array(fitted), channel)
                        for name, channel in policy.fit.STRESS.items()}
    return {"scoring_basis": "authored eligibility ceiling, no measured writer or delivery probabilities",
            "ceiling": values, "marginal_gains": edges,
            "compared_archived_bank_labels": list(known), "replay": cases,
            "fitted_artifact_sha256": sha256(archive.read_bytes()).hexdigest()}


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(run(), indent=2))
