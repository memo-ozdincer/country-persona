"""Audit the selection trade-off against a fixed rule with optimistic coordination."""
import json
from itertools import combinations
from pathlib import Path
from statistics import mean

import numpy as np

from loss_aware import HERE, RATES, channel, old, reward


def optimistic(counts, caps, local, edges, delivery):
    same = old.options(counts, caps)
    conditioned = [np.array(weights, dtype=float) for weights in local]
    for i, a, j, b, value in edges:
        conditioned[i][a] += value * delivery[j]
        conditioned[j][b] += value * delivery[i]
    return tuple(int(np.argmax([sum(score[i] for i in actions) for actions in choices]))
                 for choices, score in zip(same, conditioned, strict=True))


def run():
    saved = json.loads((HERE / "results.json").read_text())
    rng = np.random.default_rng(old.EVAL_SEED)
    noise = np.random.default_rng(old.EVAL_SEED + 8000)
    synthetic = []
    for row in saved["held_rows"]:
        local = [rng.integers(0, 8, n) for n in old.COUNTS]
        edges = [(i, int(rng.integers(old.COUNTS[i])), j, int(rng.integers(old.COUNTS[j])), int(rng.integers(0, 15)))
                 for i, j in combinations(range(3), 2)]
        rate = noise.choice(RATES, 3)
        sample = channel(old.COUNTS, old.CAPS, local, edges, rate)
        optimum = float(sample[3].max())
        assert abs(optimum - row["joint_oracle"]) <= 1e-9
        policy = optimistic(old.COUNTS, old.CAPS, local, edges, rate)
        synthetic.append(reward(sample, policy))
    archive = {}
    for name, counts, caps, local, edges, evaluate in old.un_cases():
        choices = old.options(counts, caps)
        report = []
        for rate, prior in zip(RATES, saved["archive"][name]["rows"], strict=True):
            rates = (rate,) * 3
            policy = optimistic(counts, caps, local, edges, rates)
            selection = [choices[i][index] for i, index in enumerate(policy)]
            value = sum(evaluate(selection, mask) * rate ** mask.bit_count() * (1 - rate) ** (3 - mask.bit_count())
                        for mask in range(8))
            row = {"rate": rate, "expected_released": value, "learned_delta": prior["expected_released"]["learned"] - value}
            if name == "tribunals":
                changed = prior["expected_released"]["old_unadjusted"] - prior["expected_released"]["local"]
                assert abs(changed - rate * (-2 + 3 * rate)) < 1e-9
                row["full_receipt_choice_delta"] = changed
            report.append(row)
        archive[name] = report
    return {"synthetic_mean": mean(synthetic), "synthetic_oracle_ties": sum(
                abs(outcome - row["joint_oracle"]) <= 1e-9 for outcome, row in zip(
                    synthetic, saved["held_rows"], strict=True)),
            "archive": archive,
            "interpretation": "Optimistic rule uses public edge stakes and receipt probabilities, without forecasting selection.",
            "sha256": {p.name: old.DIGEST(p) for p in (Path(__file__), HERE / "results.json")}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
