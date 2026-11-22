"""Compare team and independent delivery under the same hidden priors."""
import argparse
import json
from pathlib import Path

import numpy as np

import routing_blind_limit as limit

base, route, digest = limit.base, limit.route, limit.digest


def compare(path):
    result = json.loads(path.read_text())
    assert result["source_hashes"]["prior_bank"] == digest(limit.PRIOR_BANK)
    archive = json.loads(limit.PRIOR_BANK.read_text())
    priors = {key: np.asarray(value) for group in ("prior_anchors", "prior_stress")
              for key, value in archive[group].items()}
    cases = {}
    for case, checksum, _, actual in base.held_out():
        row = result["cases"][case]
        prior_section = archive["historical"][case]
        assert prior_section["source_sha256"] == checksum
        weights = row["exact_pricing_certificate"]["prior_mixture"]
        assert set(weights) == set(priors)
        assert np.isclose(sum(weights.values()), 1.) and min(weights.values()) >= 0.
        mixture = sum(weights[name] * p for name, p in priors.items())
        offset = sum(weights[name] * prior_section["results"][name]["independent"] for name in priors)
        silent = route.best_silent(mixture, route.receipt_matrix(actual, route.TRAIN_LOSS))
        upper = route.evaluate(silent, mixture, actual, route.TRAIN_LOSS)["net"] - offset
        lower = row["worst_gain_lower"]
        cases[case] = {"worst_case_team_feasible_lower": lower, "worst_case_independence_upper": upper,
                       "minimum_improvement_in_worst_case": lower - upper}
    return {
        "scope": "Both teams and independent comparators must select one public policy mixture without prior "
                 "identity. Both are graded by their worst regret relative to the same per-prior oracle. "
                 "Exact best silent under the fixed dual mixture bounds all prior-blind independent mixtures. "
                 "This is a retrospective typed-protocol capacity comparison using realized bank values.",
        "blind_limit_sha256": digest(path), "cases": cases,
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("blind_limit", type=Path)
    print(json.dumps(compare(cli.parse_args().blind_limit), indent=2))
