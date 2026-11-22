"""Compare proof admission before routing with release checks after routing."""
import argparse
import json
from pathlib import Path

import numpy as np

import unifil_span_review as review

study, route = review.study, review.route
DEFAULT = review.transport.OUT / "assessment.json"


def project(prior, admitted):
    accepted = route.STATES & admitted
    restricted = np.zeros_like(prior)
    np.add.at(restricted, (accepted[:, None], accepted[None, :]), prior)
    assert np.isclose(prior.sum(), restricted.sum())
    discarded = np.flatnonzero((route.STATES & ~admitted) != 0)
    assert not restricted[discarded, :].any() and not restricted[:, discarded].any()
    return restricted


def report(path):
    source = json.loads(path.read_text())
    bank = source["counterfactuals"]["missing_brazil"]
    mask = 7 & ~int(route.BITS[1])
    values = np.asarray(bank["receipt_values"])
    assert np.array_equal(values, values[route.STATES & mask])
    fit_path = review.transport.FIT
    assert study.common.runner.digest(fit_path) == source["policy_sha256"]
    policy = study.common.as_policy(json.loads(fit_path.read_text())["policy"])
    results = {}
    for name, prior in route.TEST_PRIORS.items():
        early_prior = project(prior, mask)
        matrix = route.receipt_matrix(values, route.TRAIN_LOSS)
        early = route.evaluate(policy, early_prior, values, route.TRAIN_LOSS)
        silence = route.evaluate(route.best_silent(early_prior, matrix), early_prior, values, route.TRAIN_LOSS)
        optimal, count = route.exact_optional(early_prior, matrix, route.TRAIN_LOSS)
        ceiling = route.evaluate(optimal, early_prior, values, route.TRAIN_LOSS)
        assert early["net"] <= ceiling["net"] + 1e-9
        assert all(np.isclose(mass, 0) for receipt, mass in enumerate(early["receipt_distribution"])
                   if receipt & ~mask)
        late = bank["priors"][name]
        results[name] = {"early_gate": early, "late_gate": late["rubric_fit"],
                         "exact_independent_after_early_gate": silence,
                         "exact_independent_after_late_gate": late["exact_independent"],
                         "early_gate_exact_optional": ceiling, "request_maps_examined": count}
    return {"scope": "Matched lost-qualifier case. Early admission exposes only locally verified proof IDs to each actor. "
                     "This does not give the actor the other inventory, missingness cause, or prior identity. "
                     "Late admission gives each actor its original inventory with gate failures at rendering.",
            "source_assessment_sha256": study.common.runner.digest(path), "admitted_mask": mask, "priors": results}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--assessment", type=Path, default=DEFAULT)
    opt = cli.parse_args()
    print(json.dumps(report(opt.assessment), indent=2))
