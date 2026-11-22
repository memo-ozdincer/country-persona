"""Test a typed fallback for uncertain language-model announcements."""
import argparse
from hashlib import sha256
import json
from math import log
from pathlib import Path

import numpy as np

from duplicate_card_language import CASES, POLICY, inputs, scorer
from duplicate_card_outcome_policy import PRIORS, archived_profiles
from duplicate_card_transport import FAULTS, simulate

MINIMUM_LOG_ODDS = log(3)


def run(directory):
    with inputs():
        rows = scorer.read(directory)
    fitted = json.loads(POLICY.read_text())
    table = np.asarray(fitted["trained_tables"]["matched"])
    values, hashes = archived_profiles()
    profiles = {"venezuela": values["venezuela_original_release"], "dprk": values["dprk_reordered_hybrid"]}
    report = {}
    for case in CASES:
        model, guarded = table.copy(), table.copy()
        details = []
        for seat in range(2):
            for inventory in range(4):
                if not inventory & 2:
                    continue
                row = rows[case, "signal", seat, inventory, 0, 0]
                scores = row["scores"]
                proposed = int(np.argmax(scores))
                margin = abs(scores[1] - scores[0])
                model[seat, inventory, 0] = proposed
                passes = margin >= MINIMUM_LOG_ODDS
                if passes:
                    guarded[seat, inventory, 0] = proposed
                details.append({"seat": seat, "inventory": inventory, "model": proposed,
                                "typed": int(table[seat, inventory, 0]), "logit_margin": margin,
                                "accepted_model_signal": passes})
        arms = {"typed": table, "model_signal_typed_delivery": model,
                "guarded_signal_typed_delivery": guarded}
        replays = {}
        for prior, distribution in PRIORS.items():
            replays[prior] = {
                condition: {arm: simulate(t, distribution, profiles[case], *FAULTS[condition])["writer"]["buffered"]
                            for arm, t in arms.items()}
                for condition in ("none", "both_10", "both_25")
            }
        report[case] = {"optional_signal_decisions": details, "priors": replays}
    return {"scope": "Post-result diagnostic on the two exposed dockets. Only physically legal announcement "
                     "choices with at least three-to-one odds bypass the typed fallback. Delivery remains typed.",
            "minimum_log_odds": MINIMUM_LOG_ODDS,
            "source_actions_sha256": sha256((directory / "actions.jsonl").read_bytes()).hexdigest(),
            "archived_scores_sha256": hashes, "results": report}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.directory), indent=2))
