"""Charge for pilot observations and evaluate stale versus recent inventory data."""
import argparse
from itertools import product
import json
from math import floor
from pathlib import Path

import numpy as np

import routing_prior_pilot as pilot

robust, base, route = pilot.robust, pilot.base, pilot.route
TRIALS, SEED = 128, 493017
PAST, RECENT = 32, 8
HORIZONS = (16, 64, 256)
TRANSITIONS = {
    "stable_swapped": ("swapped_desks", "swapped_desks"),
    "desk_reassignment": ("asymmetric", "swapped_desks"),
    "field_reassignment": ("asymmetric", "shifted_fields"),
    "duplication_to_complementarity": ("more_duplicates", "mostly_complementary"),
    "complementarity_to_duplication": ("mostly_complementary", "more_duplicates"),
}


def histogram(samples):
    return np.eye(64, dtype=int)[samples].sum(axis=1).reshape(TRIALS, 8, 8)


def pilot_windows(before, after, rng):
    old = rng.choice(64, size=(TRIALS, PAST), p=before.ravel())
    new = rng.choice(64, size=(TRIALS, PAST), p=after.ravel())
    return {
        "stale32": (histogram(old), PAST),
        "mixed24_plus8": (histogram(np.column_stack((old[:, RECENT:], new[:, :RECENT]))), PAST),
        "fresh8": (histogram(new[:, :RECENT]), RECENT),
        "fresh32": (histogram(new), PAST),
    }


def economic(values, baseline, count):
    gain = values - baseline
    delta = float(gain.mean())
    collection = count * 2 * route.DELIVERY_COST
    return {"mean_future_gain_before_collection": delta, "p10_future_gain": float(np.quantile(gain, .1)),
            "assumed_collection_cost": collection,
            "strict_mean_break_even_episodes": floor(collection / delta) + 1 if delta > 1e-9 else None,
            "profit": {str(n): {"mean_after_collection": float((n * gain - collection).mean()),
                                "positive_trials": int((n * gain > collection + 1e-9).sum())}
                       for n in HORIZONS}}


def evaluate(path, symmetry_path):
    prior_data = json.loads(path.read_text())
    fair_coin = json.loads(symmetry_path.read_text())
    assert fair_coin["prior_report_sha256"] == base.space.runner.digest(path)
    truth = {key: np.asarray(p) for group in ("prior_anchors", "prior_stress") for key, p in prior_data[group].items()}
    rng = np.random.default_rng(SEED)
    plans = {tag: pilot_windows(truth[old], truth[new], rng) for tag, (old, new) in TRANSITIONS.items()}
    tables = np.asarray(list(product(*(np.flatnonzero(row) for row in route.SEND))))
    records = {}
    for name, checksum, intended, observed in base.held_out():
        seed_case = prior_data["historical"][name]
        assert checksum == seed_case["source_sha256"] == fair_coin["historical"][name]["source_sha256"]
        planned_matrix = route.receipt_matrix(intended, route.TRAIN_LOSS)
        actual_matrix = route.receipt_matrix(observed, route.TRAIN_LOSS)
        policy = [base.space.as_policy(x) for x in seed_case["pool"].values()]
        public_cells = np.stack([pilot.cell_returns(x, planned_matrix) for x in policy])
        observed_cells = np.stack([pilot.cell_returns(x, actual_matrix) for x in policy])
        planned = np.concatenate((public_cells, public_cells.transpose(0, 2, 1)))
        actual = np.concatenate((observed_cells, observed_cells.transpose(0, 2, 1)))
        cases = {}
        for tag, (history, future) in TRANSITIONS.items():
            target = truth[future]
            true_net = np.einsum("plr,lr->p", actual, target)
            baseline = seed_case["results"][future]
            symmetric = fair_coin["historical"][name]["results"][future]["symmetric_routing"]
            scores = {}
            for window, (counts, count) in plans[tag].items():
                assert np.all(counts.sum(axis=(1, 2)) == count)
                estimate = (counts + pilot.UNIFORM_MASS / 64) / (count + pilot.UNIFORM_MASS)
                expected = np.einsum("plr,tlr->tp", planned, estimate)
                selected = expected.argmax(axis=-1)
                estimated_silent, realized_silent = pilot.silent_fitted(planned_matrix, actual_matrix, estimate, target, tables)
                assert max(realized_silent) <= baseline["independent"] + 1e-9
                use_library = expected[np.arange(TRIALS), selected] >= estimated_silent - 1e-9
                values = np.where(use_library, true_net[selected], realized_silent)
                scores[window] = {
                    "mean_gain_over_same_pilot_independence": float((values - realized_silent).mean()),
                    "versus_symmetric_no_pilot": economic(values, symmetric, count),
                    "versus_exact_independence": economic(values, baseline["independent"], count),
                    "versus_robust_no_pilot": economic(values, baseline["robust_mixture"], count),
                    "requester_flipped_in_portfolio": int((use_library & (selected >= len(policy))).sum()),
                }
            cases[tag] = {"history": history, "evaluation": future, "scores": scores}
        records[name] = cases
    return {"scope": "Synthetic change in joint inventory distribution between past pilot and future episodes. "
                     "Recent observations share the future distribution. Selection uses intended rubrics and "
                     "joint inventory counts, with stated uniform shrinkage. Each charged pilot observation "
                     "assumes two disclosures priced like two delivery messages. This is a scenario cost.",
            "pilot_trials": TRIALS, "seed": SEED, "horizons": list(HORIZONS),
            "input_sha256": {p.name: base.space.runner.digest(p) for p in (path, symmetry_path)},
            "scorer_sha256": base.space.runner.digest(Path(__file__)), "cases": records}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--input", type=Path, default=robust.OUT / "report.json")
    cli.add_argument("--symmetry", type=Path, default=robust.OUT / "symmetry.json")
    args = cli.parse_args()
    print(json.dumps(evaluate(args.input, args.symmetry), indent=2))
