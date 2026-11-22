"""Hold routing weights fixed and separate semantic errors from delivery limits."""
from collections import defaultdict
from hashlib import sha256
import json

import facilitator_policy_transfer as study

HERE = study.HERE
ARCHIVE = HERE / "facilitator-policy-transfer-evidence/results.json"


def report():
    observed = study.protocol.delivery.load(ARCHIVE)
    balanced, uniform = (study.policy(path) for path in (study.FROZEN, study.OLD))
    operations = {name: (name, balanced) for name in ("learned", "learned_erased", "greedy", "greedy_erased")}
    operations["uniform_fit"] = "learned", uniform
    by_prior = {}
    for prior_name, old in observed["replay"].items():
        prior = study.base.base.roster(prior_name)
        conditions = {}
        for name, (variant, weights) in operations.items():
            exact = defaultdict(float)
            empirical = defaultdict(float)
            for panel in observed["panels"]:
                truth = tuple(panel["true_relations"])
                current = tuple(panel["observed_relations"])
                for readings, results in ((truth, exact), (current, empirical)):
                    row, masks = study.base.distribution(variant, weights, prior, truth, readings)
                    for received, mass in masks.items():
                        actual = study.base.decision(truth, received)
                        proposed = study.base.decision(readings, received)
                        results["true_retain"] += mass * (actual == proposed == "retain") / 8
                        results["true_revise"] += mass * (actual == proposed == "revise") / 8
                        results["false_action"] += mass * (proposed != "withhold" and actual != proposed) / 8
                    results["cost"] += row["cost"] / 8
            for row in (exact, empirical):
                row["net"] = row["true_retain"] + row["true_revise"] - row["false_action"] - row["cost"]
            assert all(abs(empirical[key]-value) < 1e-9 for key, value in old[name].items())
            assert exact["false_action"] == 0.
            potential = empirical["true_retain"] + empirical["true_revise"] - empirical["false_action"]
            threshold = study.base.FEE * potential / empirical["cost"]
            conditions[name] = {"perfect_source_read": dict(exact), "measured_source_read": dict(empirical),
                                "break_even_send_fee_against_silence": threshold}
        by_prior[prior_name] = conditions
    return {"scope": "Exact perfect-reading intervention on frozen previously trained policies. "
                     "The fee sensitivity holds the policy and send rates fixed. Silence has net zero.",
            "input_sha256": sha256(ARCHIVE.read_bytes()).hexdigest(), "replay": by_prior}


if __name__ == "__main__":
    print(json.dumps(report(), indent=2))
