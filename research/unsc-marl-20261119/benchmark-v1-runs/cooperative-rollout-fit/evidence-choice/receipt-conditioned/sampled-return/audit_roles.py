"""Check which speaker choices explain differences in released documentary points."""
import json
from itertools import product
from statistics import mean

import sampled_team as experiment


def audit():
    saved = json.loads((experiment.HERE / "results.json").read_text())
    held = saved["held_rows"]
    comparisons = (
        ("sampled_content", "exact_content"),
        ("sampled_content", "sampled_open"),
        ("sampled_content", "fixed_content"),
        ("earlier_and_third_fit_only", "sampled_content"),
        ("earlier_and_third_fit_only", "fixed_content"),
    )
    changes = {}
    for arm, control in comparisons:
        delta = [row[arm] - row[control] for row in held]
        changes[f"{arm}__vs__{control}"] = {
            "mean": mean(delta), "wins": sum(value > 1e-9 for value in delta),
            "losses": sum(value < -1e-9 for value in delta),
            "ties": sum(abs(value) <= 1e-9 for value in delta),
        }
    reform = experiment.reform
    transfer = []
    for order, indices in reform.ORDERS.items():
        _, _, _, _, records = reform.setup(indices)
        for row in (entry for entry in saved["transfer_rows"] if entry["order"] == order):
            rate, share = row["delivery"], row["private_prior"]
            arms = row["policies"]

            def score(later, third):
                return sum((share if card == 0 else 1-share) *
                           rate ** mask.bit_count() * (1-rate) ** (3-mask.bit_count()) *
                           records[later[card + 1 if mask & 2 else 0], card, third][mask]
                           for card, mask in product(range(2), range(8)))

            a, c = arms["sampled_content"]["by_view"], arms["sampled_content"]["third"]
            f, g = arms["fixed_content"]["by_view"], arms["fixed_content"]["third"]
            gain = {
                "later_fit_only_minus_fixed": score(a, g) - score(f, g),
                "third_fit_only_minus_fixed": score(f, c) - score(f, g),
                "exact_later_repair": max(score(policy, c) for policy in product(range(2), repeat=3)) - score(a, c),
                "exact_third_repair": max(score(a, move) for move in range(2)) - score(a, c),
            }
            assert abs(score(a, c) - arms["sampled_content"]["released"]) < 1e-9
            assert abs(score(f, g) - arms["fixed_content"]["released"]) < 1e-9
            ceiling_gap = arms["content_ceiling"]["released"] - score(a, c)
            transfer.append({"order": order, "delivery": rate, "private_prior": share,
                             "ceiling_gap": ceiling_gap, "changes": gain})
    return {"results_sha256": experiment.old.DIGEST(experiment.HERE / "results.json"),
            "synthetic_paired_changes": changes, "transfer": transfer}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
