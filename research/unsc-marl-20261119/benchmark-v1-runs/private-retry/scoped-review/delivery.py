"""Price observed source review outcomes over three receipt distributions."""
import json
from math import isclose
from pathlib import Path

HERE = Path(__file__).resolve().parent
FEES = (0.15, 0.75)
ARMS = ("format", "fallback", "pooled", "scoped", "exact")


def mass(mask, p):
    n = mask.bit_count()
    return p**n * (1 - p)**(3 - n)


def replay(data):
    results = {}
    for law, rates in (("independent-40", (.4,)), ("independent-80", (.8,)),
                       ("shared-40-or-80", (.4, .8))):
        weights = {mask: sum(mass(mask, p) for p in rates) / len(rates) for mask in range(8)}
        assert isclose(sum(weights.values()), 1.)
        summary = {arm: dict(released=0., calls=0.) for arm in ARMS}
        for order in ("forward", "reverse"):
            for mask in weights:
                probability = weights[mask] / 2
                options = data["deployments"][f"{order}/{mask}"]
                reviews = [sub for sub in (3, 5, 6, 7)
                           if sub & mask == sub and data["archive"][f"{order}/{sub}"]["format"]]
                for arm, values in summary.items():
                    assert options[arm]["mask"] & mask == options[arm]["mask"]
                    values["released"] += probability * options[arm]["actual"]
                summary["pooled"]["calls"] += probability * (2 * len(reviews))
                summary["scoped"]["calls"] += probability * (2 * sum(sub.bit_count() for sub in reviews))
        fixed = max(summary[arm]["released"] for arm in ("format", "fallback"))
        for arm, values in summary.items():
            values["net"] = {fee: values["released"] - fee * values["calls"] for fee in FEES}
            values["break_even_vs_best_fixed"] = ((values["released"] - fixed) / values["calls"]
                                                  if values["calls"] and values["released"] > fixed else None)
            assert values["released"] <= summary["exact"]["released"] + 1e-10
        results[law] = summary
    return results


if __name__ == "__main__":
    print(json.dumps(replay(json.loads((HERE / "results.json").read_text())), indent=2))
