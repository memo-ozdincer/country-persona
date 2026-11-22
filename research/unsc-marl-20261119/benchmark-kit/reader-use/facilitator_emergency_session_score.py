"""Score the emergency-session records and apply the locked one-pair rule."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import facilitator_emergency_session as study
import facilitator_guard_calibrated_fit as fit

route = fit.route
MASKS = (0, 1, 2, 4)
PAIRS = (3, 5, 6)


def records(directory):
    with patch.multiple(fit.unama.study, verify=study.verify, packet=study.packet):
        return fit.unama.views(directory)


def policy_order_net(policy, prior, values, orders, erase=False):
    return [route.evaluate(policy, prior, fit.unama.reordered(values, order), fit.LOSS, force_missing=erase)["net"]
            for order in orders]


def calibration(singletons, policy):
    assert set(singletons) == set(MASKS)
    vector = np.zeros(8)
    for mask, points in singletons.items():
        vector[mask] = points
    proxy = fit.surrogate(vector)
    ties = fit.calibrated_orders(vector)
    uniform = route.TEST_PRIORS["uniform"]
    mass = route.evaluate(policy, uniform, np.zeros(8), fit.LOSS)["receipt_distribution"]
    spread = {}
    for pair in PAIRS:
        rates = [sum(mass[n] for n in PAIRS if sum(1 << order[i] for i in range(3) if n & (1 << i)) == pair)
                 for order in ties]
        spread[pair] = max(rates) - min(rates)
    probe = max(PAIRS, key=spread.get)
    return proxy, ties, spread, probe if spread[probe] > 1e-12 else None


def choose(proxy, ties, expected_probe, revealed, policy):
    assert set(revealed) == ({expected_probe} if expected_probe is not None else set())
    for mask, score in revealed.items():
        proxy[mask] = score
    rates = policy_order_net(policy, route.TEST_PRIORS["uniform"], proxy, ties)
    return [order for order, rate in zip(ties, rates, strict=True) if max(rates) - rate <= 1e-9], rates


def evaluate(score):
    previous = fit.load(study.FIT)
    fitted = {name: tuple(np.asarray(x) for x in row["policy"]) for name, row in previous["training"].items()}
    adaptive = fitted["fit_guarded"]
    singletons = {m: score[f"normalized/{m}"]["guarded_points"] for m in MASKS}
    proxy, ties, spreads, probe = calibration(singletons, adaptive)
    revealed = {probe: score[f"normalized/{probe}"]["guarded_points"]} if probe is not None else {}
    additive = proxy.copy()
    selected, predicted = choose(proxy, ties, probe, revealed, adaptive)
    actual = np.asarray([score[f"normalized/{m}"]["guarded_points"] for m in range(8)])
    evaluation = {}
    for name in ("uniform", "correlated_duplicates"):
        prior = route.TEST_PRIORS[name]
        controls = {}
        scenarios = {"singletons": additive, "one_pair": proxy, "hindsight": actual}
        for tag, values in scenarios.items():
            matrix = route.receipt_matrix(values, fit.LOSS)
            independent = route.best_silent(prior, matrix)
            query, _ = route.exact_optional(prior, matrix, fit.LOSS)
            controls[tag] = {arm: route.evaluate(policy, prior, actual, fit.LOSS)
                             for arm, policy in (("independent", independent), ("adaptive", query))}
        arms = {
            **{label: policy_order_net(policy, prior, actual, ties) for label, policy in fitted.items()},
            "fixed_script": policy_order_net(route.scripted(), prior, actual, ties),
            "selected_guarded": policy_order_net(adaptive, prior, actual, selected),
            "selected_erased": policy_order_net(adaptive, prior, actual, selected, erase=True),
        }
        averages = {arm: float(np.mean(results)) for arm, results in arms.items()}
        assert max(averages.values()) <= controls["hindsight"]["adaptive"]["net"] + 1e-9
        evaluation[name] = {"net_by_order": arms, "net_mean": averages, "exact_planners": controls}
    return {"singles": singletons, "tied_orders": ties, "pair_delivery_spread": spreads,
            "revealed_pair": revealed, "additional_calibration_reviews": len(revealed),
            "predicted_net_by_tied_order": predicted, "selected_orders": selected,
            "proxy_with_reveal": proxy.tolist(), "published": evaluation}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    p.add_argument("--marks", type=Path)
    args = p.parse_args()
    all_records = records(args.directory)
    if args.marks:
        marks = fit.load(args.marks)
        assert marks.keys() == all_records.keys()
        with patch.object(fit.unama.study, "packet", study.packet):
            scores = {key: fit.unama.score_record(record, marks[key]) for key, record in all_records.items()}
        print(json.dumps({"scores": scores, "transfer": evaluate(scores)}, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(all_records, indent=2, ensure_ascii=False))
