"""Replay the same local evidence after reversing role and opening order."""
from collections import Counter
from itertools import product
import json
from pathlib import Path
import runpy

HERE = Path(__file__).resolve().parent
T = runpy.run_path(str(HERE / "transfer.py"))
load, Policy, episode = (T[k] for k in ("load", "Policy", "episode"))


def audit():
    data = load(HERE / "evidence/metrics.json")
    normal = load(T["CASE"])
    case = {**normal, "roles": list(reversed(normal["roles"]))}
    policy = Policy({tuple(obs): move for obs, move in load(T["POLICY"])["policy"]})
    ids = [p["id"] for p in case["options"]]
    counts, traces = Counter(), {}
    for variant in ("france-overlap", "france-impasse"):
        cards = ("russia", variant)
        truth = [T["MENUS"][card] for card in cards]
        local = [{k: data["package_predictions"][card][k] for k in ids} for card in cards]
        for method, raw in data["published_scope_candidates"].items():
            scopes = {card: set(s) for card, s in raw.items()}
            for opening in product(*(sorted(menu) for menu in truth)):
                for label, strategy in (("strong", Policy()), ("learned", policy)):
                    prior = data["paths"][f"{variant}/{method}/{label}/{''.join(reversed(opening))}"]
                    route = episode(case, cards, opening, local, truth, scopes, strategy)
                    condition = variant, method, label
                    counts[*condition, "original_slots"] += prior["slots"]
                    counts[*condition, "reversed_slots"] += route["slots"]
                    counts[*condition, "state_changes"] += prior["public"]["state"] != route["public"]["state"]
                    counts[*condition, route["public"]["state"]] += 1
                    traces["/".join((*condition, "".join(opening)))] = route
    return {"scope": "Post-run robustness control. Same private cards, packages and frozen policies. Reverse role order and the two explicit openings.",
            "counts": {"/".join(k): v for k, v in counts.items()}, "paths": traces}


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
