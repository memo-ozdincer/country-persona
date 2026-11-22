"""Transfer frozen bundle policies to larger menus with more missing observations."""
import json
from pathlib import Path

import bundle_policy as policy


def evaluate(path):
    raw = json.loads(path.read_text())
    table = {(tuple(key[0]), *key[1:]): value for key, value in raw["policy"]}
    seed = 891541
    larger = policy.sp.panels((8, 9), seed, 1000, 4)
    return {
        "recipe": {"widths":[8,9],"missing_signs_per_role":4,"seed":seed,"paths_per_class":2000},
        "policy_sha256":policy.sha256(path.read_bytes()).hexdigest(),
        "reliable":policy.results(larger,table),
        "missing_returns":policy.results(policy.refit.drop_returns(larger,seed+1),table),
    }


if __name__ == "__main__":
    path = Path(__file__).with_name("evidence") / "bundle-policy/results.json"
    print(json.dumps(evaluate(path),indent=2))
