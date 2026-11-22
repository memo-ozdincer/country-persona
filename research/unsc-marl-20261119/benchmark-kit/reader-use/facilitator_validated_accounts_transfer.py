"""Replay archived joint request/reply fits against three observed reward banks."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

import facilitator_channel_fit as fit
import facilitator_validated_accounts as study


def run(scores):
    saved_path = fit.EVIDENCE / "results.json"
    public_path = study.fixed.free.source.EVIDENCE / "results.json"
    old_path = study.fixed.EVIDENCE / "results.json"
    weights = json.loads(saved_path.read_text())
    assert "resolution_2699" not in weights["training_families"]
    declared = np.array(json.loads(public_path.read_text())["points_by_record"])
    banks = {"validated": scores["released_bank"],
             "rewrite": json.loads(old_path.read_text())["released_bank"]}
    conditions = {}
    for prior_name in fit.live.PRIORS:
        prior = fit.ROUTE.TEST_PRIORS[prior_name]
        opener, opening = fit.context(declared, prior)
        policies = {name: fit.action_policy(weights[name], declared, opening, fit.PERFECT)
                    for name in ("clean", "robust")}
        policies["initial"] = fit.action_policy(fit.OLD.INITIAL, declared, opening, fit.PERFECT)
        policies["exact_independent"] = fit.exact(declared, opening, fit.PERFECT, independent=True)
        policies["exact_declared"] = fit.exact(declared, opening, fit.PERFECT)
        rows = {}
        for label, values in banks.items():
            points = np.array(values)
            options = {**policies, "exact_observed": fit.exact(points, opening, fit.PERFECT)}
            result = {}
            for name, tail in {**options, "robust_erased_request": options["robust"]}.items():
                row = fit.measure(tail, opener, opening, prior, points, fit.PERFECT,
                                  erase=name == "robust_erased_request")
                mass = np.array(row["receipt_mass"])
                row["release_probability"] = float(mass @ (points > 0))
                row["expected_requests"] = float(opening.sum((0, 1)) @ (tail[0] != 0))
                row["policy"] = [x.tolist() for x in tail]
                result[name] = row
            assert all(r["net"] <= result["exact_observed"]["net"] + 1e-9 for r in result.values())
            rows[label] = result
        conditions[prior_name] = rows
    paths = (Path(__file__).resolve(), study.EVIDENCE / "policy-protocol.md", saved_path,
             public_path, old_path, Path(fit.__file__).resolve())
    return {"training_families": weights["training_families"], "archived_updates_per_fit": weights["updates_per_fit"],
            "results": conditions, "sha256": {str(p.relative_to(study.HERE)): sha256(p.read_bytes()).hexdigest()
                                            for p in paths}}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("scores", type=Path)
    args = p.parse_args()
    print(json.dumps(run(json.loads(args.scores.read_text())), indent=2))
