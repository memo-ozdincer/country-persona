"""Compare raw and mandate-checked decisions of the same budget-aware fit."""

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT/"research/council_workshop"))
import budget_policy as study


def gated(weights):
    select = study.greedy(weights)

    def choose(rows, selected, public, seat, feats):
        legal = [(row, values) for row, values in zip(rows, feats, strict=True)
                 if row[0] != "accept" or values[1]]
        actions, features = zip(*legal)
        return select(actions, selected, public, seat, features)
    return choose


def run():
    archive = json.loads((HERE/"results.json").read_text())
    for path, digest in archive["plan"]["pins"].items():
        assert sha256((ROOT/path).read_bytes()).hexdigest() == digest
    weights = archive["training"]["variable_budget_aware"]["weights"]
    raw = study.greedy(weights)
    checked = gated(weights)
    _, held = study.core.pools()
    cohorts = study.core.held_worlds(held, study.HELD_SEED)
    reports = {}
    for cap in study.HELD_CAPS:
        report = {}
        for cohort, instances in cohorts.items():
            counts = Counter()
            for instance, record in zip(instances, archive["outcomes"][str(cap)][cohort], strict=True):
                observed, trajectory = study.core.rollout(instance, raw, True, turn_cap=cap,
                                                          context=study.budget_features)
                assert observed == record["policies"]["variable_budget_aware"]
                constrained, changes = study.core.rollout(instance, checked, True, turn_cap=cap,
                                                          context=study.budget_features)
                assert constrained["outcome"] != "invalid_agreement"
                for kind, log in (("raw", trajectory), ("checked", changes)):
                    for options, feats, choice, _ in log:
                        forbidden = choice[0] == "accept" and not feats[options.index(choice)][1]
                        counts[f"{kind}_forbidden_accepts"] += int(forbidden)
                assert counts["checked_forbidden_accepts"] == 0
                counts[f"raw_{observed['outcome']}"] += 1
                counts[f"checked_{constrained['outcome']}"] += 1
                counts["new_success"] += int(constrained["reward"] > observed["reward"])
                counts["lost_success"] += int(constrained["reward"] < observed["reward"])
            report[cohort] = dict(sorted(counts.items()))
        reports[str(cap)] = report
    return reports


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
