"""Score the scoped consultation reason and replay it with the prior Japan clause."""
import argparse
from collections import Counter
import json
from pathlib import Path

from duplicate_card_atomic import EVIDENCE, hashes as atomic_hashes, observations as atomic_observations
from duplicate_card_atomic_review import decide, probe_budget, read_probes, replay
from duplicate_card_qualifier import ORDERS, entries, hashes, observations
from duplicate_card_semantic_review import read_all


def unique_role(japan, china):
    if japan == china:
        return 0
    return 1 if japan else 2


def report(directory):
    raw, checksum = read_probes(directory, observations(), hashes())
    atoms, atom_checksum = read_probes(EVIDENCE / "atomic-dprk", atomic_observations(), atomic_hashes())
    bundled, _ = read_all(EVIDENCE / "semantic")
    readings, decoys, scores = {}, [], Counter()
    for source, variant, _, truth in entries():
        decisions = []
        for index in range(len(ORDERS)):
            row = raw[source, variant, index]
            # A maximum shared by two labels is an unresolved call.
            best = [label for label, score in zip(row["legal"], row["scores"], strict=True)
                    if score == max(row["scores"])]
            decisions.append(best[0] if len(best) == 1 else None)
        agreement = decisions[0] if len(set(decisions)) == 1 else None
        answer, frequency = Counter(decisions).most_common(1)[0]
        majority = answer if frequency >= 2 else None
        scores.update(agreements=int(agreement is not None), agreed_correct=int(agreement == truth),
                      majority_correct=int(majority == truth),
                      label_errors=sum(answer != truth for answer in decisions))
        qualifier = {"reason_truth": truth, "reason_decisions": decisions, "reason_agreement": agreement,
                     "reason_majority_posthoc": majority}
        key = ("dprk", source, variant)
        if key not in bundled:
            decoys.append({"key": key, **qualifier})
            continue
        atom = decide(atoms, source, variant)
        japan = atom["votes"][1] == [1, 1]
        readings[key] = {**bundled[key], **atom, **qualifier, "oracle": bundled[key]["truth"],
                         "split_reader": unique_role(japan, agreement == 1),
                         "split_reader_majority_posthoc": unique_role(japan, majority == 1)}

    readers = ("all_orders_agree", "clause_agreement", "split_reader", "split_reader_majority_posthoc", "oracle")
    totals = {}
    for reader in readers:
        row = Counter(correct=0, unsupported=0, missed_complete=0)
        for r in readings.values():
            truth, found = r["truth"], r[reader]
            row.update(correct=int(truth == found), unsupported=int(found != 0 and truth != found),
                       missed_complete=int(truth != 0 and truth != found))
        totals[reader] = row
    return {
        "scope": "Adaptive exposed DPRK diagnostic. The routing replay combines the prior Japan clause "
                 "with the new three-way China qualifier. Only the China reason is tested on the two decoys. "
                 "The complete source requirements and the downstream writer are unchanged.",
        "actions_sha256": checksum,
        "reused_atomic_actions_sha256": atom_checksum,
        "budget": {
            "new_probe": probe_budget(raw.values()),
            "composite_on_archived_passages": probe_budget(
                [row for key, row in atoms.items() if key[2] == 1] +
                [row for key, row in raw.items() if ("dprk", *key[:2]) in readings]
            ),
        },
        "qualifier_accuracy": scores,
        "passage_accuracy": totals,
        "passage_readings": [{"key": key, **row} for key, row in readings.items()],
        "synthetic_scope_controls": decoys,
        "evaluations": replay(readings, readers),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(report(args.directory), indent=2))
