"""Replay fitted routing with a frozen policy on locally observed contradictions."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_withhold_fit as fit


def guarded(learned, frozen):
    assert learned.keys() == frozen.keys()
    table = {}
    for state in learned:
        _, (holding, acknowledgment) = state
        visible = holding if acknowledgment is None else (*holding, acknowledgment)
        fallback = any(relation == "contradicts" for _, relation in visible)
        table[state] = frozen[state] if fallback else learned[state]
    return table


def run(artifact):
    old = json.loads(artifact.read_text())
    _, controls, _ = fit.archive.datasets()
    primary, _ = fit.extracts.receipt_bank(json.loads(fit.EXTRACTS.read_text()))
    truth = fit.reference_relations()
    banks = {"source_extracted": primary}
    banks.update((name, fit.transfer.augmented(fit.full_scope(controls[name], truth)))
                 for name in ("guinea_libya_exposed", "haiti_mali"))
    frozen, _ = fit.ceiling.stock()
    policies = []
    for name, previous in old["fits"].items():
        freeze = fit.ceiling.compiled.freeze
        weights = {freeze(row["state"]): row["probabilities"] for row in previous["weights"]}
        policies.extend(((f"fit_{name}", "learned", weights),
                         (f"guarded_{name}", "learned", guarded(weights, frozen))))
    outcomes = {}
    with patch.object(fit.record, "MODES", (fit.MODE,)):
        for name, bank in banks.items():
            outcomes[name] = {}
            for layout, baseline in old["tests"][name].items():
                replay = fit.record.evaluate(bank, policies, layout)
                arms = {}
                for policy, rows in replay.items():
                    row = rows["summary"][fit.MODE]
                    value = {**row, "full_record_net": row["brief_net"] + row["usable_withhold"]}
                    if policy.startswith("fit_"):
                        assert value == baseline["means"][policy]
                    assert value["full_record_net"] <= baseline["ceilings"]["full_record"]["adaptive"] + 1e-9
                    arms[policy] = {"mean": value, "cases": rows["cases"]}
                outcomes[name][layout] = arms
    return {
        "scope": "Post hoc replay on the same cases used to diagnose lost revisions. Each desk sees only its "
                 "own frozen-reader labels and the existing acknowledgment. The frozen policy handles any state "
                 "with an observed contradiction. The remaining states keep fitted probabilities. No additional fit.",
        "results": outcomes,
        "sha256": {path.name: sha256(path.read_bytes()).hexdigest() for path in (Path(__file__), artifact)},
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    print(json.dumps(run(parser.parse_args().artifact), indent=2, ensure_ascii=False))
