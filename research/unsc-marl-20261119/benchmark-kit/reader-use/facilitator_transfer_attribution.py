"""Attribute the routing transfer loss to policy components and missing observations."""
import argparse
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_transfer_fit as fitted
from facilitator_scope_rules import VOTE_CLAIM


def freeze(value):
    return tuple(map(freeze, value)) if isinstance(value, list) else value


def table(rows):
    return {freeze(row["state"]): row["action_probabilities"] for row in rows}


def hybrid(first, second):
    return {key: (first if key[0] == "first" else second)[key]
            for key in first.keys() | second.keys()}


def reward_key(case):
    sequence = (frozenset(), frozenset({0}), frozenset({1}), frozenset({0, 1}))
    return tuple(fitted.record.rewards(case["receipts"][mask])[1] for mask in sequence)


def current_scores(cases, layout, controls):
    with patch.object(fitted.record, "MODES", (fitted.MODE,)):
        values = fitted.record.evaluate(cases, controls, layout)
    return {name: result["summary"][fitted.MODE] for name, result in values.items()}


def grouped_ceiling(bank, layout, groups):
    total = 0.0
    for group in groups:
        visible = {key: bank[key] for key in group}
        _, _, payoff = fitted.ceiling.tensor(visible, layout, True)
        total += len(group) * fitted.exact.maximize(payoff)["exact_net"] / len(bank)
    return total


def claim_kinds(guinea_libya):
    grouping = defaultdict(list)
    if guinea_libya:
        for panel, _, predicate, _, cards in fitted.recent.study.panels():
            exact_vote = all(VOTE_CLAIM.fullmatch(f"{actor} {predicate}.") for actor, _ in cards)
            grouping["recorded_vote" if exact_vote else "source_statement"].append((panel, fitted.MODE))
    return grouping


def run(artifact):
    previous = json.loads(artifact.read_text())
    learned = table(previous["policy_tables"]["adaptive"])
    frozen, _ = fitted.ceiling.stock()
    assert frozen.keys() == learned.keys()
    controls = tuple((name, "learned", params) for name, params in (
        ("frozen", frozen), ("trained", learned), ("trained_sender", hybrid(learned, frozen)),
        ("trained_responder", hybrid(frozen, learned)),
    ))
    train, cohorts = fitted.split()
    report = {}
    for cohort, cases in cohorts.items():
        rows = {}
        kinds = claim_kinds(cohort == "guinea_libya") or {"recorded_vote": list(cases)}
        assert {key for keys in kinds.values() for key in keys} == cases.keys()
        for layout in ("split", "overlap"):
            scores = current_scores(cases, layout, controls)
            old = previous["results"][cohort][layout]
            for key, label in (("trained", "trained_adaptive"), ("frozen", "frozen")):
                assert scores[key] == old["systems"][label]["summary"][fitted.MODE]
            frozen_net = scores["frozen"]["brief_net"]
            trained_net = scores["trained"]["brief_net"]
            sender = scores["trained_sender"]["brief_net"]
            responder = scores["trained_responder"]["brief_net"]
            sender_contribution = ((sender - frozen_net) + (trained_net - responder)) / 2
            responder_contribution = ((responder - frozen_net) + (trained_net - sender)) / 2
            assert abs(sender_contribution + responder_contribution - (trained_net - frozen_net)) < 1e-10
            best_observable = old["bounds"]["adaptive"]["exact_net"]
            best_case_conditioned = grouped_ceiling(cases, layout, ((key,) for key in cases))
            best_kind_conditioned = grouped_ceiling(cases, layout, kinds.values())
            assert best_case_conditioned + 1e-10 >= best_kind_conditioned >= best_observable - 1e-10
            rows[layout] = {"scores": scores, "sender_contribution": sender_contribution,
                            "responder_contribution": responder_contribution,
                            "exact_without_case_identity": best_observable,
                            "exact_with_claim_kind": best_kind_conditioned,
                            "exact_with_case_identity": best_case_conditioned}
        groups = defaultdict(list)
        for (panel, _), case in cases.items():
            groups[case["reads"]].append({"panel": panel, "receipt_payoffs": reward_key(case)})
        collisions = [{"observed_relations": reads, "cases": entries}
                      for reads, entries in groups.items() if len({r["receipt_payoffs"] for r in entries}) > 1]
        report[cohort] = {"rosters": rows, "observational_collisions": collisions,
                          "claim_kinds": {kind: [key[0] for key in keys] for kind, keys in kinds.items()}}
    return {"scope": "Retrospective component swaps from the same two tables. The case-conditioned ceiling "
                     "is a privileged upper bound: it supplies the case identity to both actors and recomputes the "
                     "exact optimum per case. A middle ceiling conditions on whether the requested claim is a vote or a statement.",
            "receipt_payoff_order": ["none", "first only", "second only", "both"],
            "fit_panel_count": len(train), "report": report,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in (Path(__file__), artifact)}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    args = parser.parse_args()
    print(json.dumps(run(args.artifact), indent=2))
