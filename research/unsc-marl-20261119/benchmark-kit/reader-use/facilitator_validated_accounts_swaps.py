"""Localize archived policy transfer gaps by replacing one component at a time."""
import argparse
import json
from pathlib import Path

import numpy as np

import facilitator_validated_accounts_transfer as transfer

fit = transfer.fit


def best_request(reply, opening, pay):
    heard_returns = np.einsum("rbm,rbtc,mtc->mt", opening, fit.D.one_hot(reply), pay)
    unmasked = heard_returns @ fit.heard(np.eye(4)).T - opening.sum((0, 1))[:, None] * fit.D.QUERY_COST
    return np.where(fit.D.CHAIR_LEGAL, unmasked, -np.inf).argmax(-1)


def best_reply(request, opening, pay):
    values = np.einsum("rbm,mt,mtc->rbtc", opening, fit.heard(fit.D.one_hot(request)), pay)
    return np.where(fit.D.FINAL_LEGAL, values, -np.inf).argmax(-1)


def run(archive, scores):
    declared = np.array(scores["released_bank"])
    assert declared.tolist() == [42, 49, 49, 56, 49, 56, 63, 70]
    ans = {}
    for prior_name, rows in archive["results"].items():
        prior = fit.ROUTE.TEST_PRIORS[prior_name]
        opener, opening = fit.context(declared, prior)
        case = rows["validated"]
        pay = fit.value(declared, fit.PERFECT)
        answer = {}
        for label in ("clean", "robust"):
            q, r = map(np.array, case[label]["policy"])
            policies = {"archived": (q, r), "replace_request": (best_request(r, opening, pay), r),
                        "replace_reply": (q, best_reply(q, opening, pay))}
            data = {}
            for name, policy in policies.items():
                metrics = fit.measure(policy, opener, opening, prior, declared, fit.PERFECT)
                metrics["expected_requests"] = float(opening.sum((0, 1)) @ (policy[0] != 0))
                metrics["policy"] = [x.tolist() for x in policy]
                data[name] = metrics
            assert abs(data["archived"]["net"] - case[label]["net"]) < 1e-10
            assert all(data["archived"]["net"] <= row["net"] + 1e-10 <= case["exact_observed"]["net"] + 2e-10
                       for row in data.values())
            answer[label] = data
        ans[prior_name] = {"exact": case["exact_observed"]["net"], "policies": answer}
    return ans


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    args = p.parse_args()
    def load(name):
        return json.loads((args.directory / name).read_text())
    print(json.dumps(run(load("transfer-apostrophe.json"), load("apostrophe.json")), indent=2))
