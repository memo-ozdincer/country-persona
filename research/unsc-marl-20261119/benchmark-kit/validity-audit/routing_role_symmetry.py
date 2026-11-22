"""Test a public coin flip for the requester desk under prior uncertainty."""
import argparse
import json
from pathlib import Path

import numpy as np

import routing_prior_robustness as robust

base, route = robust.base, robust.route
TOL = 1e-9


def symmetric(prior):
    return (prior + prior.T) / 2


def report(path):
    archive = json.loads(path.read_text())
    anchors = {k: np.asarray(p) for k, p in archive["prior_anchors"].items()}
    evaluation = {**anchors, **{k: np.asarray(p) for k, p in archive["prior_stress"].items()}}
    cases = {}
    for name, checksum, intended, observed in base.held_out():
        original = archive["historical"][name]
        assert checksum == original["source_sha256"]
        # The requester and responder are protocol roles. Either desk can take either role.
        pool = {key: base.space.as_policy(p) for key, p in original["pool"].items()}
        planned = route.receipt_matrix(intended, route.TRAIN_LOSS)
        comparator = np.array([
            robust.portfolio.contrasts.measure(route.best_silent(p, planned), intended, p)["net"]
            for p in anchors.values()
        ])
        for key, prior in anchors.items():
            pool[f"sym_independent_{key}"] = route.best_silent(symmetric(prior), planned)
        public = np.array([robust.at_prior(pool, intended, symmetric(p)) for p in anchors.values()])
        gain = public - comparator[:, None]
        lower, chosen = robust.maximin(gain)
        dual, worst = robust.maximin(-gain.T)
        assert abs(lower + dual) <= TOL
        observed_matrix = route.receipt_matrix(observed, route.TRAIN_LOSS)
        rows = {}
        for key, p in evaluation.items():
            value = float(robust.at_prior(pool, observed, symmetric(p)) @ chosen)
            peer, count = route.exact_optional(symmetric(p), observed_matrix, route.TRAIN_LOSS)
            bound = robust.portfolio.contrasts.measure(peer, observed, symmetric(p))["net"]
            assert value <= bound + TOL
            previous = original["results"][key]
            rows[key] = {"symmetric_routing": value, "fixed_desk_routing": previous["robust_mixture"],
                         "nominal_uniform": previous["nominal_uniform"], "independent_oracle": previous["independent"],
                         "exact_symmetric_query": bound, "request_maps_examined": count}
        assert abs(rows["asymmetric"]["symmetric_routing"] - rows["swapped_desks"]["symmetric_routing"]) <= TOL
        cases[name] = {"selection": robust.signed_policy(pool, chosen), "planned_worst_gain": lower,
                       "planned_dual_upper": -dual, "worst_weight": dict(zip(anchors, worst.tolist(), strict=True)),
                       "source_sha256": checksum, "results": rows}
    return {"scope": "One public fair coin before inventory draws assigns the requester desk. "
                     "Choose a single mixture of learned and independent tables using only the public rubric "
                     "and the three original anchor priors. The swapped desks and other stress distributions "
                     "are evaluated separately. Independence is free to use the known evaluation prior.",
            "prior_report_sha256": base.space.runner.digest(path), "historical": cases}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--input", type=Path, default=robust.OUT / "report.json")
    args = cli.parse_args()
    print(json.dumps(report(args.input), indent=2))
