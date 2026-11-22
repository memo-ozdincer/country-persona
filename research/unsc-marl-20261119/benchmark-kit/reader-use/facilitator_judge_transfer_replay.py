"""Compare retained-draft decision rules on model and reviewed labels."""
import argparse
from hashlib import sha256
import json
from unittest.mock import patch

import numpy as np

import facilitator_judge_transfer as test

pairs, fit = test.pairs, test.pairs.fit
D, trained = fit.D, pairs.trained
MODES = ("primary", "all_positive", "both_positive")


def select(first, second, verdicts, challenge, mode):
    data = {name: np.zeros((4, 4)) for name in ("apparent", "reviewed", "material_error", "calls",
                                                "judge_input_tokens", "judge_output_tokens")}
    data["apparent"][:, 0] = data["reviewed"][:, 0] = 1
    chosen = {}
    for q, replies in enumerate(second):
        for c in range(1, 4):
            pair = [first[c], replies[c]]
            keys = [test.old.key(c, row["reply"], row["ended"]) for row in pair]
            approved = [verdicts[k]["strict_pass"] for k in keys]
            screened = approved if mode == "all_positive" or (mode == "both_positive" and all(approved)) else [False] * 2
            merits = [yes and (not extra or challenge[k]["clear"])
                      for k, yes, extra in zip(keys, approved, screened, strict=True)]
            data["calls"][q, c] = 2 + sum(screened)
            for side in ("input_tokens", "output_tokens"):
                data["judge_" + side][q, c] = sum(verdicts[k][side] + (challenge[k][side] if extra else 0)
                                                       for k, extra in zip(keys, screened, strict=True))
            idx = next((i for i, flag in enumerate(merits) if flag), None)
            chosen[f"{q}/{c}"] = {"chosen": keys[idx] if idx is not None else None,
                                 "screened": [k for k, extra in zip(keys, screened, strict=True) if extra],
                                 "oracle_can_select": any(row["passed"] for row in pair)}
            if idx is not None:
                data["apparent"][q, c] = 1
                data["reviewed"][q, c] = int(pair[idx]["passed"])
                data["material_error"][q, c] = int(bool(pair[idx]["assessment"]["errors"]))
    assert (data["reviewed"] <= data["apparent"]).all()
    return data, chosen


def run_scenario(points, first, second, weights, primary, challenge):
    result = {}
    points = np.asarray(points)
    for mode in MODES:
        data, trace = select(first, second, primary, challenge, mode)
        scores = {}
        for label in fit.live.PRIORS:
            prior = fit.ROUTE.TEST_PRIORS[label]
            opener, opening = fit.context(points, prior)
            ref = fit.exact(points, opening, data["reviewed"], independent=True)
            policies = {"exact_no_request": ref}
            for name, parameters in weights["policies"].items():
                policies[name + "_fit"] = fit.action_policy(parameters["weights"], points, opening,
                                                            np.asarray(parameters["feature_channel"]))
            scored = {}
            for name, action in policies.items():
                q, r = action
                mass = np.einsum("rbm,mt,rbtc->tc", opening, fit.heard(D.one_hot(q)), D.one_hot(r))
                score = fit.measure(action, opener, opening, prior, points, data["reviewed"])
                proposed = fit.measure(action, opener, opening, prior, points, data["apparent"])
                scored[name] = {"audited_net": score["net"], "apparent_net": proposed["net"],
                                "invalid_delivery_probability": float((mass * (data["apparent"] - data["reviewed"])).sum() * (1 - D.LOSS)),
                                "material_error_delivery_probability": float((mass * data["material_error"]).sum() * (1 - D.LOSS)),
                                "expected_author_calls": float(2 * mass[:, 1:].sum()),
                                "expected_judge_calls": float((mass * data["calls"]).sum()),
                                **{f"expected_{key}": float((mass * data[key]).sum())
                                   for key in ("judge_input_tokens", "judge_output_tokens")}}
                assert proposed["net"] >= score["net"] - 1e-10
            for row in scored.values():
                row["audited_advantage_over_no_request"] = row["audited_net"] - scored["exact_no_request"]["audited_net"]
            cost = data["calls"] + 2 * (np.arange(4) != 0)
            value = fit.value(points, data["reviewed"])
            fitted = scored["ideal_fit"]
            for price in (.2, 1.):
                with patch.object(fit, "value", lambda *_: value - price * cost):
                    quiet = fit.exact(points, opening, data["reviewed"], independent=True)
                net = fit.measure(quiet, opener, opening, prior, points, data["reviewed"])["net"]
                mass = np.einsum("rbm,mt,rbtc->tc", opening, fit.heard(D.one_hot(quiet[0])), D.one_hot(quiet[1]))
                quiet_net = net - price * (mass * cost).sum()
                learned_net = fitted["audited_net"] - price * (fitted["expected_author_calls"] + fitted["expected_judge_calls"])
                fitted.setdefault("price_sensitivity", {})[str(price)] = {
                    "net_over_reoptimized_no_request": float(learned_net - quiet_net)}
            scores[label] = scored
        result[mode] = {"selection": trace,
                        "admission": {k: m.tolist() for k, m in data.items() if k in ("apparent", "reviewed", "material_error")},
                        "scores": scores}
    return result


def run(primary, challenge, weights):
    bank = test.gather()
    assert bank.keys() == primary.keys()
    assert challenge.keys() == {k for k, r in primary.items() if r["strict_pass"]}
    def confusion(screened):
        return {f"{int(ref)}{int(yes)}": sum(v["passed"] == ref and
                     (primary[k]["strict_pass"] and (not screened or challenge[k]["clear"])) == yes for k, (_, v) in bank.items())
                for ref in (False, True) for yes in (False, True)}
    return {"confusion_reviewed_then_positive": {"primary": confusion(False), "all_positive": confusion(True)},
            "scenarios": {name: run_scenario(points, first, second, weights, primary, challenge)
                          for name, points, first, second in pairs.contexts() if name.startswith("2719_")}}


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    files = (test.EVIDENCE / "first.json", test.EVIDENCE / "challenge.json",
             test.HERE / "facilitator-measured-channel-evidence/fits.json")
    result = run(*(trained.read(p) for p in files))
    result["sha256"] = {str(p.relative_to(test.HERE)): sha256(p.read_bytes()).hexdigest() for p in files}
    print(json.dumps(result, ensure_ascii=False, indent=2))
