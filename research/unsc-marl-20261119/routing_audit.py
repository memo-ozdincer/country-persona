"""Isolate learned routing actions and retain a deciding paired transcript."""
from collections import Counter
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import routing_fit as fit

RULES = {
    "set_deferral": {(-3, 0)},
    "focused_request": {(0, 1)},
}
FRESH_HOLDOUT_SEED = 977341


def actors(results):
    weights = {int(action): np.asarray(row) for action, row in results["models"]["fixed_continuation"].items()}
    policy = fit.actor(weights, results["validation"]["fixed_continuation"]["selected"])

    def restricted(permitted):
        def choose(obs, legal, default):
            move = policy(obs, legal, default)
            return move if (default, move) in permitted else default
        return choose

    return {"fixed": fit.no_override, "full_actor": policy,
            **{name: restricted(actions) for name, actions in RULES.items()}}


def samples():
    with patch.object(fit, "SEEDS", new={**fit.SEEDS, "heldout": FRESH_HOLDOUT_SEED}):
        yield "fresh_synthetic", fit.synth("heldout", (7, 8), 170, 3)
    base = fit.transfer.load(fit.VENEZUELA/"evidence/model-receipt/metrics.json")
    model = base["conditions"]["pooled"]
    yield "venezuela_model_receipts", fit.archived(list(fit.model_receipt.input_rows(
        model["signs_before_admission"], model["scope_before_admission"], "modeled")))
    yield "myanmar", fit.archived(list(fit.episode.canonical.myanmar(0)))
    yield "mali", fit.archived(list(fit.episode.canonical.mali(fit.transfer.load(
        fit.transfer.MALI/"evidence/joint-transfer/metrics.json"), 0)))


def scope_trace(item, terms, receipt, actor):
    public_events = []
    execute = fit.router.play

    def captured(*args, **kwargs):
        return execute(*args, **kwargs, events=public_events)

    with patch.object(fit.router, "play", new=captured):
        metrics, changes = fit.simulate(item, terms, receipt, actor)
    _, _, local, opening, _ = item[0]
    before = fit.router.sp.opened(opening, local)
    per_role = [0,0]
    for i, signs in enumerate(before):
        per_role[i//2] += signs.bit_count()
    for event in public_events:
        for role, sign, bits in event["disclosed"]:
            per_role[role] += bits.bit_count()
    return {"counts": metrics, "policy_changes": changes, "opening_ledger": before,
            "events": public_events, "admitted_propositions_per_role": per_role}


def audit(results):
    ready = actors(results)
    comparisons, examples = {}, {}
    for family, panels in samples():
        comparisons[family] = {}
        for condition, rows in panels.items():
            scored = {arm: fit.collect(rows, policy) for arm,policy in ready.items()}
            base = scored["fixed"][2]
            reports = {}
            for name, (_, metrics, paths) in scored.items():
                matched = Counter((fit.world_label(item), str(a[0]), str(b[0]))
                                  for (item, _, _),a,b in zip(rows, base, paths, strict=True))
                reports[name] = {**metrics, "paired": fit.router.sp.flatten(matched)}
            comparisons[family][condition] = reports
            if family == "fresh_synthetic":
                continue
            for outcome in ("gain", "loss"):
                direction = (False, True) if outcome == "gain" else (True, False)
                for index, ((item, terms, receipt), start, end) in enumerate(zip(
                        rows, base, scored["full_actor"][2], strict=True)):
                    if (start[0], end[0]) != direction:
                        continue
                    examples[f"{family}/{condition}/{outcome}"] = {
                        "row": index, "world_outcome": fit.world_label(item), "options": terms,
                        "traces": {arm: scope_trace(item, terms, receipt, actor) for arm,actor in ready.items()},
                    }
                    break
    return {"scope": "Post-hoc action masks. Test menu draws for the synthetic panel are fresh. The same named-family fault tapes are reused.",
            "fresh_synthetic_seed": FRESH_HOLDOUT_SEED, "results": comparisons, "witnesses": examples}


if __name__ == "__main__":
    import sys

    results = json.loads(Path(sys.argv[1]).read_text())
    print(json.dumps(audit(results), indent=2))
