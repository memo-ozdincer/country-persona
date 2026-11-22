"""Replay a source-claim judge against archived, previously scored recipient masks."""
from collections import defaultdict
from hashlib import sha256
import json

import facilitator_source_relation as study

base = study.prior.witness.transfer.base
load = study.protocol.delivery.load
HERE = study.HERE
JUDGED = HERE / "facilitator-source-relation-evidence/results.json"
WITNESS = study.prior.routing.ARTIFACT


def score():
    archive = load(WITNESS)["reads"]
    judged = load(JUDGED)["decisions"]
    policy = study.prior.witness.transfer.policy(study.prior.witness.transfer.FROZEN)
    cases = list(base.cases())
    panel_keys = [(docket, n) for docket, group in study.protocol.SIDES.items() for n, _ in enumerate(group)]
    observed = {}
    for (docket, n), (truth, _, briefs) in zip(panel_keys, cases, strict=True):
        keys = [f"{docket}/{n}/{i}" for i in range(2)]
        assert [archive[key]["claim"] for key in keys] == list(study.protocol.SIDES[docket][n])
        assert tuple(archive[key]["expected"] for key in keys) == truth
        assert len(briefs) == 4 and briefs[-1]["expected_disposition"] == base.decision(truth, base.TARGETS)
        quotes = tuple(archive[key]["admitted"] for key in keys)
        direct = tuple(judged.get(f"routed/{key}", {}).get("stable_relation", "unknown") for key in keys)
        agreement = tuple(now if now == then else "unknown" for now, then in zip(direct, quotes, strict=True))
        observed[docket, n] = {"quote_only": quotes, "direct": direct, "agreement": agreement,
                               "authored_relations": truth}
    result = {}
    for inventory in ("overlap", "split"):
        result[inventory] = {}
        for policy_name in ("learned", "learned_erased", "greedy"):
            totals = {mode: defaultdict(float) for mode in next(iter(observed.values()))}
            for (truth, _, briefs), variants in zip(cases, observed.values(), strict=True):
                for mode, measured in variants.items():
                    stats, masks = base.distribution(policy_name, policy, base.base.roster(inventory), truth, measured)
                    value = totals[mode]
                    value["send_cost"] += stats["cost"] / len(cases)
                    for mask, probability in masks.items():
                        brief = briefs[2 * int(0 in mask) + int(1 in mask)]
                        gold = base.decision(truth, mask)
                        action = base.decision(measured, mask)
                        assert brief["expected_disposition"] == gold
                        mass = probability / len(cases)
                        value["false_action"] += mass * (action != "withhold" and action != gold)
                        value[f"usable_{gold}"] += mass * (action == gold and brief["arms"]["frozen_source_reader"]["strict"])
            result[inventory][policy_name] = totals
    files = (JUDGED, WITNESS, base.CITATIONS, study.prior.witness.transfer.FROZEN)
    return {"scope": "Archived Haiti and Mali facilitator replacements. A brief counts only when the "
                     "routed disposition matches what the received evidence warrants and the archived prose "
                     "passed its existing review. No new prose and no reclassification of that review.",
            "source_sha256": {str(p.relative_to(HERE)): sha256(p.read_bytes()).hexdigest() for p in files},
            "panel_relations": [{"panel": key, "variants": values} for key, values in observed.items()],
            "replay": result}


if __name__ == "__main__":
    print(json.dumps(score(), indent=2))
