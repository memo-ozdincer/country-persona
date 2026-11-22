"""Audit public-opening transfer and replay a singleton-informed calibration."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import torch

import facilitator_third_delivery_context as context
import facilitator_guard_calibrated_fit as archive

delivery = context.delivery
route = context.route


def restored(state):
    matrices = [state[f"{i}.weight"] for i in (0, 2, 4)]
    network = torch.nn.Sequential(torch.nn.Linear(len(matrices[0][0]), len(matrices[0])), torch.nn.Tanh(),
                                  torch.nn.Linear(len(matrices[1][0]), len(matrices[1])), torch.nn.Tanh(),
                                  torch.nn.Linear(len(matrices[2][0]), len(matrices[2])))
    network.load_state_dict({k: torch.as_tensor(v, dtype=torch.float32) for k, v in state.items()})
    return network.eval()


def compare(learned, public, actual, prior, previous):
    left, right, _, features = context.context(public, prior)
    exact_independent = delivery.exact_independent(prior, context.terminal(public))
    exact_tail, _ = context.diagnose.exact_tail(left, right, prior, context.terminal(public))
    frozen = context.tail(learned, features, (left, right))
    _, _, scripted_chair, scripted_reply = delivery.scripts()
    plans = {
        "matched_frozen": frozen, "matched_previous_tail": (left, right, *previous[2:]),
        "matched_script": (left, right, scripted_chair, scripted_reply),
        "matched_exact_tail": exact_tail, "matched_exact_independent": exact_independent,
    }
    results = {}
    for label, plan in plans.items():
        context.diagnose.audit(plan, prior)
        results[label] = delivery.measure(plan, prior, actual)
    results["matched_frozen_erased"] = delivery.measure(frozen, prior, actual, erase=True)
    return results


def rank_contrast(net):
    """Hold the opening and singleton weights fixed when a pair becomes valuable."""
    prior = route.TEST_PRIORS["uniform"]
    anchor = context.rubric(34, (7, 7, 7))
    left, right, _, shared = context.context(anchor, prior)
    tasks = [context.rubric(34, (7, 7, 7), pair, 15) for pair in (3, 6)]
    common, _ = context.diagnose.exact_tail(left, right, prior,
                                            np.mean([context.terminal(p) for p in tasks], axis=0))
    rows = []
    learned = []
    for pair, points in zip((3, 6), tasks, strict=True):
        local = shared.copy()
        local[:8] = (context.terminal(points) - points[0]) / 36.
        policy = context.tail(net, local, (left, right))
        stop, _ = context.diagnose.exact_tail(left, right, prior, context.terminal(points))
        estimates = {
            arm: delivery.measure(used, prior, points)["net"]
            for arm, used in (("learned", policy), ("exact_shared", common), ("exact_conditioned", stop))
        }
        rows.append({"pair": pair, "points": points.tolist(), "net": estimates})
        learned.append(policy)
    return {"rows": rows, "learned_tables_identical": all(np.array_equal(a, b)
                                                          for a, b in zip(*learned, strict=True)),
            "min_shared_mean_regret": sum(r["net"]["exact_conditioned"] - r["net"]["exact_shared"]
                                          for r in rows) / len(rows)}


def run(path):
    saved = json.loads(path.read_text())
    original = json.loads((context.THIS_EVIDENCE / "fit.json").read_text())
    previous = tuple(np.asarray(p) for p in original["training"]["learned_query"]["policy"])
    net = restored(saved["network"])
    _, cases = context.cases()
    results = {}
    for name, (public, actual) in cases.items():
        # No paired or full receipt labels enter this estimator. For modular
        # assembly, independent admission predicts linear contributions.
        calibration = archive.surrogate(actual[[0, 1, 2, 0, 4, 0, 0, 0]])
        report = {}
        for prior_label in ("uniform", "correlated_duplicates"):
            prior = route.TEST_PRIORS[prior_label]
            declared = compare(net, public, actual, prior, previous)
            assert declared["matched_frozen"] == saved["transfer"][name]["priors"][prior_label]["arms"]["learned"]
            revised = compare(net, calibration, actual, prior, previous) if name in ("unama", "emergency") else None
            report[prior_label] = {"declared": declared, "singleton_calibration": revised}
        results[name] = {"singleton_calibration": calibration.tolist(),
                         "calibration_matches_hidden_pairs": np.array_equal(calibration, actual),
                         "results": report}
    return {
        "scope": "Opening/last-stage policy swap and post hoc singleton calibration on two modular writer banks. "
                 "The declaration uses published rubric weights. Calibration sees only empty and singleton grades. "
                 "A separate synthetic test changes the complementarity reward without changing the opening.",
        "results": results, "fixed_opening_pair_contrast": rank_contrast(net),
        "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in (Path(__file__), Path(context.__file__), path)},
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fit", type=Path)
    print(json.dumps(run(parser.parse_args().fit), indent=2, ensure_ascii=False))
