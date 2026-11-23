"""Audit blocking incompatible signatures and publishing checked exclusions."""

from collections import Counter
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]/"research/council_workshop"))
import crossplay as study


def run():
    result = json.loads((HERE/"results.json").read_text())
    _, held = study.core.pools()
    cohorts = study.core.held_worlds(held, result["plan"]["cohort_seed"])
    weights = result["fits"]["mixed"]["weights"]
    output = {}
    for name, worlds in cohorts.items():
        if name == "new_3_seat":
            continue
        stats = {}
        for protection in ("none", "reject_signature", "certify_exclusion"):
            counts = Counter()
            for instance in worlds:
                for fixed in instance[0]:
                    unavailable = study.reachable_diagnostic("eager", instance, fixed)

                    def choose(rows, selected, public, seat, feats):
                        if seat != fixed:
                            return study.select(rows, feats, weights)
                        if protection == "none" or feats[0][1]:
                            return ("accept", selected), None
                        counts["denied_signatures"] += 1
                        if protection == "certify_exclusion" and ("rule_out", selected) in rows:
                            counts["published_exclusions"] += 1
                            return ("rule_out", selected), None
                        return ("yield_floor", selected), None

                    state, _ = study.core.rollout(instance, choose, turn_cap=study.CAP,
                                                  context=study.budget.budget_features)
                    counts[state["outcome"]] += 1
                    if state["reward"] and unavailable == "partner_holds_required_exclusion":
                        counts["recovered_required_exclusion"] += 1
            stats[protection] = dict(sorted(counts.items()))
        raw = result["evaluation"][name]["eager"]["methods"]["mixed"]
        for label in ("valid_agreement","certified_impasse","invalid_agreement","unresolved"):
            assert stats["none"].get(label, 0) == sum(row.get(label, 0) for row in raw.values())
        assert all(panel.get("invalid_agreement", 0) == 0
                   for label,panel in stats.items() if label != "none")
        output[name] = stats
    return output


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
