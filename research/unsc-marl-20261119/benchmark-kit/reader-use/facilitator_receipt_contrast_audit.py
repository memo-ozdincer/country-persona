"""Audit payoff trade-offs and the value of a privileged evidence check."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import facilitator_claim_type_fit as design


def changes(before, after):
    keys = ("brief_net", "send_cost", "false_action", "usable_retain", "usable_revise")
    delta = {key: after[key] - before[key] for key in keys}
    assert abs(delta["brief_net"] - (delta["usable_retain"] + delta["usable_revise"] -
                                     delta["false_action"] - delta["send_cost"])) < 1e-9
    increase = delta["false_action"]
    return {"deltas": delta, "break_even_false_action_penalty":
            1 + delta["brief_net"] / increase if increase > 0 else None}


def privileged_labels(bank):
    source = json.loads(design.prior.OLD_TEST.read_text())["source_relations"]
    informed = {}
    for (panel, mode), row in bank.items():
        correct = tuple(source[f"{panel}/S{i}"]["expected"] == source[f"{panel}/S{i}"]["literal"] for i in (1, 2))
        informed[panel, mode] = row | {"reads": tuple(zip(row["reads"], correct, strict=True))}
    return informed


def audit(path):
    saved = json.loads(path.read_text())
    _, bank, kind = design.datasets()
    cohort = "guinea_libya_exposed"
    test = bank[cohort]
    labeled = design.prior.augmented(privileged_labels(test))
    kind |= {f"{p}/swapped": value for p, value in kind.items()}
    result = {}
    comparisons = {}
    for name, layouts in saved["transfer"].items():
        comparisons[name] = {}
        for layout, values in layouts.items():
            metrics = values["overall"]
            comparisons[name][layout] = changes(metrics["type_original"], metrics["type_plus_pairs"])
    for layout in ("split", "overlap"):
        upper = design.ceilings(labeled, kind, layout)
        before = saved["transfer"][cohort][layout]["ceilings"]
        assert all(upper[p][m] + 1e-9 >= before[p][m] for p in before for m in before[p])
        result[layout] = {"original": before, "adjudicated_label_correctness_bit": upper}
    return {
        "scope": "Primary deltas use both document orders and original rewards. Break-even reprices the false-action "
                 "penalty for fixed policies. The oracle exposes the scored correctness of each local relation to "
                 "its holder and, after acknowledgment, to the other actor. Chairs and rewards stay fixed. "
                 "The correctness bit is a privileged diagnostic.",
        "changes_vs_old_type_fit": comparisons,
        "guinea_libya_information_ceilings": result,
        "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in (Path(__file__), path)},
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("results", type=Path)
    print(json.dumps(audit(p.parse_args().results), indent=2))
