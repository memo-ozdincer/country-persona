"""Test public claim type as an observation for two learned routing desks."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
from unittest.mock import patch

import numpy as np

import facilitator_transfer_fit as prior

MODE = prior.MODE
record = prior.record
base = prior.base
optimizer = base.base.optimizer
VOTE = re.compile(r"^(?:voted\s|abstained\s)", re.I)
KINDS = ("vote", "statement")


def identify(verbs):
    return "vote" if all(VOTE.match(verb) for verb in verbs) else "statement"


def datasets():
    historical, exposed = prior.split()
    train = historical | {key: row for key, row in exposed["space_gaza_bound"].items()
                          if key[0].startswith("space/")}
    legacy = prior.record.collect(row for row in prior.record.development()
                                  if row[0].startswith(("haiti-", "mali-")) and row[1] == "quote")
    controls = {
        "guinea_libya_exposed": exposed["guinea_libya"],
        "gaza_bound": {key: row for key, row in exposed["space_gaza_bound"].items() if key[0].startswith("gaza/")},
        "haiti_mali": prior.mode_bank(legacy, "quote"),
    }
    instruments = {
        f"{family}-{i}": predicates
        for family, items in record.dev.transfer.PANELS.items()
        for i, (_, predicates, _) in enumerate(items)
    }
    instruments.update((name, (predicate, predicate))
                       for name, _, predicate, _, _ in record.transfer.panels())
    clarifications = prior.ceiling.compiled.study.prior.source_inputs
    instruments.update((name, (predicate, predicate)) for name, _, predicate, *_ in clarifications())
    instruments.update((name, (predicate, predicate))
                       for name, _, predicate, _, _ in prior.recent.study.panels())
    for family, groups in base.endpoint.SIDES.items():
        for i, group in enumerate(groups):
            actors = ("China", "The three African members") if family == "haiti" else ("France", "Russia")
            assert all(claim.startswith(actor + " ") for actor, claim in zip(actors, group, strict=True))
            instruments[f"{family}-{i}"] = tuple(claim.removeprefix(actor + " ")
                                                 for actor, claim in zip(actors, group, strict=True))
    for label, _ in exposed["space_gaza_bound"]:
        instruments[label] = ("voted on the specified text",) * 2
    assert not set(train) & set().union(*(set(bank) for bank in controls.values()))
    assert len(train) == 16 and {k: len(v) for k, v in controls.items()} == {
        "guinea_libya_exposed": 6, "gaza_bound": 4, "haiti_mali": 6,
    }
    used = train.keys() | set().union(*(bank.keys() for bank in controls.values()))
    kind = {key[0]: identify(instruments[key[0]]) for key in used}
    return train, controls, kind


def divide(bank, kind):
    return {source: {key: value for key, value in bank.items() if kind[key[0]] == source}
            for source in KINDS}


def fit_conditional(partitions, fallback):
    states, actions, rewards, masses, trained_views = {}, [], [], [], {}
    n = sum(map(len, partitions.values()))
    width = 0
    for kind, bank in partitions.items():
        views, choices, outcomes, mass = record.training_batch(bank)
        states.update({(kind, view): (offset + width, slots) for view, (offset, slots) in views.items()})
        trained_views[kind] = {view for view, (offset, slots) in views.items()
                               if any(np.any(choices == index) for index in range(offset, offset + slots))}
        actions.append(choices + width)
        rewards.append(outcomes["brief"])
        masses.append(mass["design_mixture"] * len(bank) / n)
        width += sum(slots for _, slots in views.values())
    choices, scores = np.concatenate(actions), np.concatenate(rewards)
    trace, fitted = optimizer.fit(states, choices, scores, {"design_mixture": np.concatenate(masses)})
    weights = base.base.observed_weights(states, fitted["joint_learned"])
    policies = {kind: {view: weights[kind, view] if view in trained_views[kind] else p
                       for view, p in fallback.items()} for kind in KINDS}
    details = {"trace": trace, "trajectory_rows": len(choices),
               "supported_states": {k: len(v) for k, v in trained_views.items()}}
    return policies, details


def scores(bank, kind, systems, layout):
    groups = divide(bank, kind)
    totals, names = {}, tuple(systems[KINDS[0]])
    for topic, cases in groups.items():
        if not cases:
            continue
        with patch.object(record, "MODES", (MODE,)):
            table = record.evaluate(cases, [(name, "learned" if name != "greedy" else "greedy", policy)
                                           for name, policy in systems[topic].items()], layout)
        totals[topic] = {name: result["summary"][MODE] for name, result in table.items()}
    first = next(iter(totals.values()))
    pooled = {name: {m: sum(len(groups[k]) * block[name][m] for k, block in totals.items()) / len(bank)
                     for m in first[name]} for name in names}
    return {"by_kind": totals, "overall": pooled}


def ceilings(bank, kind, layout):
    results = {}
    for protocol, groups in (("relation_only", [bank]), ("claim_type", divide(bank, kind).values())):
        results[protocol] = {}
        for name, ack in (("adaptive", True), ("independent", False)):
            score = 0.0
            for group in groups:
                if group:
                    _, _, grid = prior.ceiling.tensor(group, layout, ack)
                    score += len(group) * prior.exact.maximize(grid)["exact_net"] / len(bank)
            results[protocol][name] = score
    return results


def run():
    train, test, kind = datasets()
    plain, plain_trace = prior.fit(prior.augmented(train), True)
    train_groups = {k: prior.augmented(group) for k, group in divide(train, kind).items()}
    conditional, condition_trace = fit_conditional(train_groups, plain)
    frozen, _ = prior.ceiling.stock()
    systems = {k: {"relation_only": plain, "claim_type": conditional[k], "frozen": frozen, "greedy": {}} for k in KINDS}
    practice = scores(prior.augmented(train), kind | {f"{p}/swapped": k for p, k in kind.items()},
                      systems, "training")
    assert abs(practice["overall"]["claim_type"]["brief_net"] - condition_trace["trace"][-1]["record_reward"]) < 1e-9
    prior.exact.check()
    outcomes = {}
    for name, bank in test.items():
        outcomes[name] = {}
        for layout in ("split", "overlap"):
            result = scores(bank, kind, systems, layout)
            upper = ceilings(bank, kind, layout)
            assert upper["claim_type"]["adaptive"] + 1e-9 >= result["overall"]["claim_type"]["brief_net"]
            assert upper["relation_only"]["adaptive"] + 1e-9 >= result["overall"]["relation_only"]["brief_net"]
            outcomes[name][layout] = result | {"ceilings": upper}

    def serialize(table):
        return [{"state": state, "probabilities": p} for state, p in table.items()]

    files = (Path(__file__), Path(prior.__file__), Path(optimizer.__file__), prior.OLD_TEST, prior.MIXED_TEST,
             record.BOUND, record.LEGACY, record.TEST, prior.ceiling.EVIDENCE, prior.ceiling.prior.RESULTS)
    return {"scope": "Fit two routing policies with exposure to the same archived rewards and role-slot augmentations. "
                     "The claim-type table sees a public binary label derived from the requested act. Unsupported states use "
                     "the relation-only fit. The three held-back cohorts are fit-family-disjoint and previously exposed. "
                     "Gulf of Guinea and Libya motivated the test. Zero language model updates. Free acknowledgments.",
            "policy_updates_per_fit": optimizer.STEPS,
            "training_cases": {p: kind[p] for p, _ in train},
            "training_types": Counter(kind[p] for p, _ in train),
            "test_cases": {label: {p: kind[p] for p, _ in rows} for label, rows in test.items()},
            "traces": {"relation_only": plain_trace, "claim_type": condition_trace},
            "practice": practice, "transfer": outcomes,
            "policy_tables": {"relation_only": serialize(plain), "claim_type": {k: serialize(v) for k, v in conditional.items()}},
            "sha256": {str(path.resolve().relative_to(prior.HERE.parents[1])): sha256(path.read_bytes()).hexdigest()
                       for path in files}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
