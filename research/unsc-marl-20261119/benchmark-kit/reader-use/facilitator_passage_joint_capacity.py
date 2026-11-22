"""Check whether the opening features can express the declared planned choices."""
import argparse
import json

import numpy as np
from scipy.optimize import linprog

import facilitator_passage_joint_fit as study

fit, R = study.fit, study.R


def constraints(archive):
    rules = [[], []]
    for docket, (points, _) in study.held().items():
        for label in fit.live.PRIORS:
            prior = R.TEST_PRIORS[label]
            features, _ = study.inputs(points, prior)
            target = archive["cases"][docket][label]["policies"]["declared_block_planner"]["team"][:2]
            for desk, (values, chosen) in enumerate(zip(features[:2], target, strict=True)):
                for inv, action in enumerate(chosen):
                    for other in np.flatnonzero(R.SEND[inv]):
                        if other != action:
                            rules[desk].append({"case": docket, "prior": label, "inventory": inv,
                                                "planned": action, "alternative": int(other),
                                                "feature_difference": (values[inv, action] - values[inv, other]).tolist()})
    return rules


def solve(rows, strict, limits=(-1., 1.)):
    problem = []
    for row in rows:
        force = strict or row["alternative"] < row["planned"]
        problem.append([-x for x in row["feature_difference"]] + [int(force)])
    result = linprog([0., 0., 0., 0., -1.], A_ub=problem, b_ub=np.zeros(len(problem)),
                     bounds=[limits] * 4 + [(0., 1.)], method="highs")
    assert result.success
    w = result.x[:4]
    return {"unit_box_margin": float(result.x[-1]), "witness_weights": w.tolist(),
            "active_constraints": sum(1 for r in rows if abs(np.dot(r["feature_difference"], w)) < 1e-10)}


def run():
    report = study.historic.read(study.EVIDENCE / "results.json")
    observations = constraints(report)
    return {
        name: {"rows": data,
               "global_strict_margin": solve(data, strict=True),
               "global_margin_with_argmax_tie_order": solve(data, strict=False),
               "by_case_and_prior": {
                   f"{case}/{prior}": solve([r for r in data if (r["case"], r["prior"]) == (case, prior)], strict=False)
                   for case, row in report["cases"].items() for prior in row
               }}
        for name, data in zip(("left", "right"), observations, strict=True)
    }


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(run(), indent=2))
