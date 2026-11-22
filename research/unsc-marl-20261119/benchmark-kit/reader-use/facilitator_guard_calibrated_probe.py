"""Replay one extra pair assessment for a frozen router on the tied UNAMA sources."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

import facilitator_guard_calibrated_fit as fit

route = fit.route


def run(path):
    archived = fit.load(path)
    policy = tuple(np.asarray(x) for x in archived["training"]["fit_guarded"]["policy"])
    held = fit.load(fit.HELD)["records"]
    actual = np.asarray([held[f"normalized/{mask}"]["guarded_points"] for mask in range(8)])
    base = fit.surrogate(actual)
    tie = fit.calibrated_orders(actual)
    assert len(tie) == 2 and tie[0][-1] == tie[1][-1]
    pairs = sorted({(1 << order[0]) | (1 << order[-1]) for order in tie})
    contexts = {}
    for name, result in archived["tests"]["normalized"].items():
        prior = route.TEST_PRIORS[name]
        probes = {}
        for mask in pairs:
            partial = base.copy()
            partial[mask] = actual[mask]
            values = {}
            for order in tie:
                label = "".join(str(i) for i in order)
                transformed = fit.unama.reordered(partial, order)
                values[label] = route.evaluate(policy, prior, transformed, fit.LOSS)["net"]
            best = max(values.values())
            selected = [label for label, value in values.items() if abs(value - best) < 1e-9]
            realized = [result["orders"][label]["arms"]["fit_guarded"]["net"] for label in selected]
            realized_erased = [result["orders"][label]["arms"]["fit_guarded_erased"]["net"] for label in selected]
            matrix = route.receipt_matrix(partial, fit.LOSS)
            independent = route.best_silent(prior, matrix)
            adaptive, _ = route.exact_optional(prior, matrix, fit.LOSS)
            probes[str(mask)] = {
                "partial_reward": partial.tolist(), "probed_value": int(actual[mask]),
                "predicted_net_by_order": values, "selected_orders": selected,
                "fitted_realized_net": sum(realized) / len(realized),
                "fitted_erased_realized_net": sum(realized_erased) / len(realized_erased),
                "same_information_independent_net": route.evaluate(independent, prior, actual, fit.LOSS)["net"],
                "same_information_adaptive_net": route.evaluate(adaptive, prior, actual, fit.LOSS)["net"],
            }
        contexts[name] = {"probes": probes, "no_pair_fit": result["calibrated_means"]["fit_guarded"],
                          "no_pair_adaptive": result["controls"]["singleton_adaptive"]["net"],
                          "full_table_adaptive_ceiling": result["controls"]["exact_adaptive"]["net"]}
    return {
        "scope": "Post hoc replay of separate single-pair calibrations. The public-only and singleton scores "
                 "remain the same. One observed pair overwrites its surrogate value. All remaining pair and "
                 "full-table values stay unavailable for selection. No new generations. Case choice, tie pattern "
                 "and mechanism were inspected previously.",
        "mask_mapping": {"1": "Norway", "2": "Russia", "4": "China"}, "evaluations": contexts,
        "sha256": {p.name: sha256(p.read_bytes()).hexdigest()
                   for p in (Path(__file__), Path(fit.__file__), path, fit.HELD)},
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("fit", type=Path)
    print(json.dumps(run(p.parse_args().fit), indent=2))
