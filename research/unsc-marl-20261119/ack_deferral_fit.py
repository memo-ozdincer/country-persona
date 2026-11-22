"""Train a one-decision deferral actor using a public delivery-status bit."""
import hashlib
import json
from unittest.mock import patch

import routing_ack as ack
import routing_audit as audit
import routing_fit as fit
import query_gate as gate

SEEDS = {"train": 943079, "dev": 736471, "heldout": 619687, "archive": fit.SEEDS["archive"]}
FEATURES = (
    "acting_role_also_saw_a_loss", "peer_offer_live", "peer_offer_known_eligible",
    "peer_offer_known_excluded", "peer_offer_unknown", "own_offer_live",
    "peer_receipt_cached", "my_receipt_cached", "few_live", "single_known_live_acceptance",
    "local_state_covers_live", "routine_is_check", "routine_is_bundle",
    "quarter_menu_unknown", "at_least_half_horizon", "quarter_menu_excluded",
)
ASK_SET = fit.selection.group.OFFER_SET
ROUTINE = ack.ROUTINE


def features(x, own_failed):
    view = dict(zip(fit.FEATURES, x[:len(fit.FEATURES)], strict=True))
    return (own_failed, *(bool(view[name]) for name in FEATURES[1:13]),
            view["own_unknown_live"]>=.25, view["horizon"]>=.5, view["own_excluded_live"]>=.25)


def candidate(_, legal, fallback):
    return ROUTINE if fallback == ASK_SET else fallback


def paired(rows):
    for item, terms, receipt in rows:
        contexts = []

        def choose(should_defer):
            def act(x, default, picked, own_lost, peer_lost):
                if contexts or not peer_lost:
                    return False
                assert (default, picked) == (ASK_SET, ROUTINE)
                contexts.append(features(x, own_lost))
                return should_defer
            return act

        fixed, _, _ = ack.play(item, terms, receipt, candidate, choose(False))
        armed = contexts[0] if contexts else None
        waited = fixed
        if armed is not None:
            contexts.clear()
            waited, changes, _ = ack.play(item, terms, receipt, candidate, choose(True))
            assert contexts == [armed] and len(changes) == 1
        yield fit.world_label(item), armed, fixed, waited


def cohort(panels):
    return {name: list(paired(rows)) for name, rows in panels.items()}


def score(panels, rules):
    return {name: {
        "fixed": gate.score(rows, lambda _: True),
        "always_defer_after_peer_failure": gate.score(rows, lambda _: False),
        "learned": gate.score(rows, lambda obs: gate.choose(obs, rules)),
    } for name, rows in panels.items()}


def evaluate():
    with patch.object(fit, "SEEDS", new=SEEDS), patch.object(gate, "FEATURES", new=FEATURES):
        train = cohort(fit.synth("train", (5, 6), 480, 2))
        dev = cohort(fit.synth("dev", (6,), 360, 3))
        rules, journal = gate.fit(train, dev)
        tests = cohort(fit.synth("heldout", (7, 8), 400, 3))
        methods = {family: score(cohort(rows), rules) for family, rows in audit.samples()
                   if family != "fresh_synthetic"}
    source = fit.VENEZUELA/"evidence/model-receipt/metrics.json"
    return {"scope": "Fit on separate synthetic team outcomes. The one-bit status is public and reliably delivered in this intervention. UN families are exposed transfer diagnostics withheld from all fitting.",
            "seeds": SEEDS, "features": FEATURES,
            "model_receipt_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "rules": rules, "fit": journal, "train": score(train, rules), "dev": score(dev, rules),
            "holdout": score(tests, rules), "workshops": methods}


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
