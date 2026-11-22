"""Compare union receipts with desk-attributed delivery logs on the same routes."""
import argparse
import json
from pathlib import Path

import numpy as np

import routing_active_receipt_probe as active

ident, base, route, robust = active.ident, active.base, active.route, active.robust


def ordered_kernel(policy):
    """Observe field delivered by each desk, including zero for nondelivery."""
    ask, send, reply = policy
    fields = route.BITS
    kernel = np.zeros((len(fields), len(fields), 8, 8))
    loss = route.TRAIN_LOSS
    for left in route.STATES:
        for right in route.STATES:
            first = send[left]
            for request, question_prob in ((ask[left], 1 - loss), (0, loss)):
                second = reply[right, request]
                for a, first_prob in ((first, 1 - loss), (0, loss)):
                    for b, second_prob in ((second, 1 - loss), (0, loss)):
                        kernel[a, b, left, right] += question_prob * first_prob * second_prob
    union = np.zeros((8, 8, 8))
    for a, first in enumerate(fields):
        for b, second in enumerate(fields):
            union[first | second] += kernel[a, b]
    assert np.allclose(union, ident.receipt_kernel(policy))
    return kernel.reshape(-1, 8, 8)


def logging_kernel(pool, selection):
    blocks = []
    for label, weight in selection.items():
        forward = .5 * weight * ordered_kernel(pool[label])
        blocks.extend((forward, forward.transpose(0, 2, 1)))
    ordered = np.concatenate(blocks).reshape(-1, 64)
    assert np.allclose(ordered.sum(axis=0), 1)
    return ordered


def pair_metrics(kernel, first, second):
    a, b = (kernel @ prior.ravel() for prior in (first, second))
    tv = float(np.abs(a - b).sum() / 2)
    affinity = float(np.sqrt(a * b).sum())
    assert tv < 1 and 0 < affinity <= 1 + 1e-10
    # The overlap of product laws yields these conservative testing bounds.
    n = active.PROBES
    return {
        "total_variation_per_episode": tv,
        "bayes_accuracy_one_episode": (1 + tv) / 2,
        "bayes_accuracy_after_eight_bounds": [
            max((1 + tv) / 2, 1 - affinity ** n / 2),
            (1 + np.sqrt(max(0, 1 - affinity ** (2 * n)))) / 2,
        ],
    }


def run(archive_path, symmetry_path, witness_path):
    archive = json.loads(archive_path.read_text())
    symmetric = json.loads(symmetry_path.read_text())
    witness = json.loads(witness_path.read_text())
    digest = base.space.runner.digest
    assert witness["input_sha256"] == {p.name: digest(p) for p in (archive_path, symmetry_path)}
    anchors = {key: np.asarray(p) for key, p in archive["prior_anchors"].items()}
    cases = {}
    for name, checksum, intended, actual in base.held_out():
        old = witness["historical"][name]
        row = archive["historical"][name]
        assert checksum == old["source_sha256"] == row["source_sha256"]
        selection = symmetric["historical"][name]["selection"]
        assert selection == old["logging_policy"]
        pool = {key: base.space.as_policy(p) for key, p in row["pool"].items()}
        matrix = route.receipt_matrix(intended, route.TRAIN_LOSS)
        for label, prior in anchors.items():
            if f"sym_independent_{label}" in selection:
                pool[f"sym_independent_{label}"] = route.best_silent((prior + prior.T) / 2, matrix)

        ordered = logging_kernel(pool, selection)
        old_metrics = pair_metrics(ordered, np.asarray(old["prior_a"]), np.asarray(old["prior_b"]))
        # Search for a new ambiguity using the richer channel, with the same rubric-only construction.
        first, second, label, separation = ident.ambiguous_pair(ordered, pool, intended)
        new_metrics = pair_metrics(ordered, first, second)
        assert new_metrics["total_variation_per_episode"] < 1e-10
        blind, _ = ident.exact_value(actual, (first + second) / 2)
        aware = max(ident.exact_value(actual, prior)[0] for prior in (first, second))
        assert aware >= blind - 1e-9
        cases[name] = {
            "source_sha256": checksum,
            "ordered_rank": int(np.linalg.matrix_rank(ordered)),
            "union_rank": old["channel_rank"],
            "previous_aliases": old_metrics,
            "ordered_aliases": {
                **new_metrics,
                "prior_a": first.tolist(), "prior_b": second.tolist(),
                "witness_policy": label, "planned_orientation_separation": separation,
                "realized_regret_without_prior": aware - blind,
            },
        }
    return {
        "scope": "Fixed symmetric incumbent. Observe the policy draw, public desk orientation, and ordered "
                 "delivered field identifiers. Compare the previously constructed union-log aliases and "
                 "search for new aliases using the richer channel. Private inventories remain hidden.",
        "cases": cases,
        "input_sha256": {p.name: digest(p) for p in (archive_path, symmetry_path, witness_path)},
        "scorer_sha256": digest(Path(__file__)),
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--anchor", type=Path, default=robust.OUT / "report.json")
    cli.add_argument("--symmetry", type=Path, default=robust.OUT / "symmetry.json")
    cli.add_argument("--witness", type=Path, default=robust.OUT / "receipt-identifiability.json")
    args = cli.parse_args()
    print(json.dumps(run(args.anchor, args.symmetry, args.witness), indent=2))
