"""Refit with a monotone authored record reward under a 92-word counterfactual."""
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
from unittest.mock import patch

import adaptive_align as align
import adaptive_fit as optimizer
import adaptive_transfer as transfer

relay = transfer.relay
archive = relay.archive


def bank_with_comparison():
    original = transfer.ftf_bank()
    updated = dict(original)
    cards = frozenset({"us", "russia", "indonesia_national"})
    comparison = archive.COMPARISON
    recorded = relay.assembly(archive.load(), tuple(relay.KEYS.index(k) for k in archive.KEYS if k in cards),
                              [archive.packet(i) for i, k in enumerate(archive.KEYS) if k in cards])
    assert not {"shared", "divergent"} & recorded["proof"].keys()
    supplement = " ".join([archive.PASSAGES[k] for k in archive.KEYS if k in cards] + [comparison])
    assert len(supplement.split()) == 92
    candidate = recorded["final_record"] + " " + comparison
    for rule in ("shared", "divergent"):
        assert archive.REQUIRED[rule] <= cards and all(span in candidate for span in archive.PROOF[rule])
    updated[cards] = {"record_points": recorded["final_record_score"] + 14, "counterfactual_record": candidate}

    def nonmonotonic(bank):
        return [(sorted(small), sorted(big), low["record_points"], high["record_points"])
                for small, low in bank.items() for big, high in bank.items()
                if small < big and low["record_points"] > high["record_points"]]
    assert len(nonmonotonic(original)) == 1 and not nonmonotonic(updated)
    return updated, nonmonotonic(original)


def scores(bank):
    return {(target, anchor, pending): bank[frozenset(relay.KEYS[i] for i in target if i not in pending)]["record_points"]
            for target, anchor in relay.SCENARIOS
            for size in range(3)
            for pending in combinations([i for i in target if i != anchor], size)}


def run():
    bank, failures = bank_with_comparison()
    with patch.object(optimizer, "scores", return_value=scores(bank)):
        states, actions, outcomes, mass = optimizer.build()
    history, policies = optimizer.fit(states, actions, outcomes, mass)
    learned = {state: policies["joint_learned"][start:start + width].tolist()
               for state, (start, width) in states.items()}
    trained = align.enrich(learned, bank)
    mapping_only = align.enrich(training_bank=bank)
    previous = align.enrich()
    files = [Path(__file__).resolve(), Path(align.__file__), Path(optimizer.__file__), transfer.FROZEN,
             Path(transfer.__file__)]
    return {"scope": "One fit on a counterfactual 92-word written-vote renderer. "
                     "The original 85-word experiment is preserved. Neither transfer docket contributes to fitting. "
                     "The new comparison is present only when both national sources support it.",
            "parent_hashes": {f.name: sha256(f.read_bytes()).hexdigest() for f in files},
            "original_regressions_on_added_evidence": failures,
            "rendered_counterfactual": next(row["counterfactual_record"] for row in bank.values()
                                            if "counterfactual_record" in row),
            "update_count": optimizer.STEPS, "fit": history,
            "transfer": {family: {"original": previous["families"][family]["average"],
                                  "changed_mapping_only": mapping_only["families"][family]["average"],
                                  "changed_mapping_and_refit": trained["families"][family]["average"]}
                         for family in trained["families"]},
            "fitted_policy": [{"local_state": state, "probabilities": values} for state, values in learned.items()]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
