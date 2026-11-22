"""Localize losses by exact one-role substitutions against a frozen partner."""
import json
from importlib.util import module_from_spec, spec_from_file_location
from itertools import product
from pathlib import Path
from statistics import mean

import numpy as np

HERE = Path(__file__).resolve().parent
spec = spec_from_file_location("reform_2553_locked_transfer", HERE / "transfer.py")
t = module_from_spec(spec)
spec.loader.exec_module(t)


def project(true, probability, observation, action, last):
    return float(sum(probability[b, mask] * true[(action[observation[b, mask]], b, last)][mask]
                     for b, mask in product(range(2), range(8))))


def run():
    saved = t.READ(HERE / "results.json")["orders"]
    output = {}
    for name, order in t.ORDERS.items():
        _, _, _, _, true = t.setup(order)
        rows = []
        for row in saved[name]["forced_private_inventory"]:
            rate, share = row["receipt"], row["first_card_probability"]
            p = np.array([share, 1 - share])[:, None] * np.array(
                [rate ** mask.bit_count() * (1-rate) ** (3-mask.bit_count()) for mask in range(8)])[None, :]
            obs = np.where(np.arange(8)[None, :] & 2, np.arange(2)[:, None] + 1, 0)

            def value(action, last):
                return project(true, p, obs, action, last)

            def late(last):
                return max(product(range(2), repeat=3), key=lambda a: value(a, last))

            def third(action):
                return max(range(2), key=lambda c: value(action, c))

            declared = row["outcomes"]["content"]["learned"]
            baseline = declared["by_view"], declared["third"]
            assert abs(value(*baseline) - declared["released"]) < 1e-9
            new_late = late(baseline[1])
            new_third = third(baseline[0])
            plans = {"frozen": baseline, "replace_later": (new_late, baseline[1]),
                     "replace_third": (baseline[0], new_third),
                     "later_then_third": (new_late, third(new_late)),
                     "third_then_later": (late(new_third), new_third)}
            scores = {k: value(*policy) for k, policy in plans.items()}
            oracle = row["outcomes"]["content"]["oracle"]["released"]
            arrival = row["outcomes"]["arrival"]["oracle"]["released"]
            assert max(scores.values()) <= oracle + 1e-9
            rows.append({"p": rate, "share": share, "outcomes": scores,
                         "policies": {k: [list(a), c] for k, (a, c) in plans.items()},
                         "arrival_oracle": arrival, "content_oracle": oracle})
        checks = {mode: {"below_arrival": sum(r["outcomes"][mode] < r["arrival_oracle"] - 1e-9 for r in rows),
                         "ties_content_oracle": sum(abs(r["outcomes"][mode] - r["content_oracle"]) <= 1e-9 for r in rows),
                         "mean_delta": mean(r["outcomes"][mode] - r["outcomes"]["frozen"] for r in rows)}
                  for mode in rows[0]["outcomes"]}
        output[name] = {"summary": checks, "rows": rows}
    return {"orders": output, "sha256": {p.name: t.old.DIGEST(p) for p in (
        Path(__file__), HERE / "repair-protocol.md", HERE / "results.json", Path(t.__file__))}}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
