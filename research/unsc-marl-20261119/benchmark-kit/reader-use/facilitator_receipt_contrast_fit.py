"""Add training-only pairs of archived contradiction receipts and test transfer."""
from collections import Counter
from hashlib import sha256
from itertools import combinations, product
import json
from pathlib import Path

import facilitator_claim_type_fit as design
from facilitator_transfer_attribution import reward_key

HERE = design.prior.HERE
MODE = design.MODE
PREVIOUS = HERE / "facilitator-claim-type-fit-evidence/results.json"


def singleton_contradictions(bank, kinds):
    candidates = {kind: [] for kind in design.KINDS}
    for (panel, _), case in bank.items():
        for slot, relation in enumerate(case["reads"]):
            if relation == "contradicts":
                row = case["receipts"][frozenset({slot})]
                assert row["action"] == "revise"
                candidates[kinds[panel]].append({"panel": panel, "slot": slot, "singleton": row})
    return candidates


def assemble(a, b):
    """Compose separate checked fields. Strict requires every received field to pass."""
    receipts = {}
    for flags in product((False, True), repeat=2):
        seen = frozenset(i for i, included in enumerate(flags) if included)
        fragments = [item["singleton"] for i, item in enumerate((a, b)) if i in seen]
        expected = "revise" if any(card["expected"] == "revise" for card in fragments) else "withhold"
        action = "revise" if seen else "withhold"
        receipts[seen] = {"expected": expected, "action": action,
                          "strict": expected == action and all(card["strict"] for card in fragments)}
    return {"reads": ("contradicts", "contradicts"), "receipts": receipts}


def contrasts(candidates):
    cases, metadata, kinds = {}, {}, {}
    for kind, candidates_of_kind in candidates.items():
        pairs = [pair for pair in combinations(candidates_of_kind, 2) if pair[0]["panel"] != pair[1]["panel"]]
        for i, (a, b) in enumerate(pairs):
            key = f"composed/{kind}/{i}"
            row = assemble(a, b)
            cases[key, MODE] = row
            kinds[key] = kind
            assert reward_key(row)[1:3] == tuple(design.record.rewards(card["singleton"])[1] for card in (a, b))
            metadata[key] = {"sources": [a, b], "receipt_payoffs": reward_key(row), "claim_type": kind}
    return cases, metadata, kinds


def frozen_controls(prior_trace):
    def freeze(val):
        return tuple(map(freeze, val)) if isinstance(val, list) else val
    return {kind: {freeze(row["state"]): row["probabilities"]
                   for row in prior_trace["policy_tables"]["claim_type"][kind]} for kind in design.KINDS}


def output():
    train, tests, kinds = design.datasets()
    refs = json.loads(PREVIOUS.read_text())
    archive = singleton_contradictions(train, kinds)
    new, metadata, inferred = contrasts(archive)
    joint = train | new
    all_kinds = kinds | inferred
    assert all(archive.values()) and len(joint) == len(train) + len(new)
    assert all(item["panel"] in refs["training_cases"]
               for m in metadata.values() for item in m["sources"])
    end_groups = {k: design.prior.augmented(rows) for k, rows in design.divide(joint, all_kinds).items()}

    relation, rel_trace = design.prior.fit(design.prior.augmented(joint), True)
    conditional, typed_trace = design.fit_conditional(end_groups, relation)
    frozen, _ = design.prior.ceiling.stock()
    old = frozen_controls(refs)
    systems = {k: {"relation_plus_pairs": relation, "type_plus_pairs": conditional[k],
                   "type_original": old[k], "frozen": frozen, "greedy": {}} for k in design.KINDS}
    all_kinds |= {f"{p}/swapped": k for p, k in all_kinds.items()}
    practice = design.scores(design.prior.augmented(joint), all_kinds, systems, "training")
    for name, trace in (("relation_plus_pairs", rel_trace), ("type_plus_pairs", typed_trace)):
        assert abs(practice["overall"][name]["brief_net"] - trace["trace"][-1]["record_reward"]) < 1e-9

    outcome = {}
    for name, bank in tests.items():
        outcome[name] = {}
        ordered = design.prior.augmented(bank)
        for layout in ("split", "overlap"):
            raw = design.scores(bank, all_kinds, systems, layout)
            assert abs(raw["overall"]["type_original"]["brief_net"] -
                       refs["transfer"][name][layout]["overall"]["claim_type"]["brief_net"]) < 1e-12
            result = design.scores(ordered, all_kinds, systems, layout)
            upper = design.ceilings(ordered, all_kinds, layout)
            assert result["overall"]["type_plus_pairs"]["brief_net"] <= upper["claim_type"]["adaptive"] + 1e-9
            outcome[name][layout] = result | {"ceilings": upper, "original_order": raw}
    files = (Path(__file__), Path(design.__file__), Path(design.prior.__file__), PREVIOUS)
    return {
        "scope": "Two matched exact routing fits on archived proposals plus compositional training rewards. "
                 "Constructed pairs combine previously audited single-card receipt outcomes. No language model "
                 "generates these pairs or their rewards. Held-back tests use their original archives, with both "
                 "source-slot assignments evaluated jointly. All families were previously exposed in the project.",
        "updates_per_fit": design.optimizer.STEPS, "original_training_proposals": len(train),
        "added_training_pairs_by_kind": Counter(inferred.values()), "added_training_pairs": metadata,
        "traces": {"relation_plus_pairs": rel_trace, "type_plus_pairs": typed_trace}, "practice": practice,
        "transfer": outcome,
        "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in files},
        "policies": {k: {kind: [{"state": s, "probabilities": p} for s, p in table.items()]
                          for kind, table in groups.items()}
                     for k, groups in (("relation_plus_pairs", {"shared": relation}), ("type_plus_pairs", conditional))},
    }


if __name__ == "__main__":
    print(json.dumps(output(), indent=2))
