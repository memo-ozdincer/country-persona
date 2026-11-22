"""Replay offer scheduling on recorded Mali evidence with independent claim validation."""
import argparse
from collections import Counter
from itertools import product
import json
from pathlib import Path
import sys

import offer_policy as engine

HERE = Path(__file__).resolve().parent
MALI = HERE.parent / "mali"
sys.path.insert(0, str(HERE.parent))
from decision_ledger import readout, truthful_disclosure


def load(p):
    return json.loads(p.read_text())


def bits(labels, names):
    return sum(1 << labels.index(name) for name in names)


def rollout(case, row, script, policy):
    n, truth, local, opening, _ = row
    labels = [p["id"] for p in case["options"]]
    full = (1 << n) - 1
    state = engine.sp.opened(opening, local)
    claims, moves = [], []

    def names(mask):
        return [label for i, label in enumerate(labels) if mask & (1 << i)]

    def publish(role, yes, no):
        if not (yes or no):
            return None
        claim = {"id": f"claim-{len(claims)+1}", "role": case["roles"][role],
                 "accepts": names(yes), "excludes": names(no)}
        assert truthful_disclosure(claim, names(truth[role]))
        claims.append(claim)
        return claim["id"]

    for role in range(2):
        moves.append({"actor": role, "action": "opening", "claim_id": publish(role, state[2*role], 0)})
    current = state, 1, 0, 3
    checks = 0
    while current[2] < n + 1 and not engine.sp.terminal(current[0], full):
        previous, role, step, _ = current
        obs, actions = engine.moves(row, current)
        action = policy.get(obs, engine.strategy(obs, script))
        current = engine.transition(row, current, action, actions)
        checks += action == engine.CHECK
        yes = current[0][2*role] & ~previous[2*role]
        no = current[0][2*role+1] & ~previous[2*role+1]
        moves.append({"actor": role, "slot": step, "action": action, "claim_id": publish(role, yes, no)})
    decision = readout(labels, case["roles"], claims)
    assert engine.sp.terminal(current[0], full) == (decision["state"] in ("AGREEMENT_POSSIBLE", "IMPASSE"))
    return {"slots": current[2], "checks": checks, "decision": decision, "moves": moves, "claims": claims}


def freeze_table(data):
    return {(tuple(key[0]), tuple(key[1]), *key[2:]): action for key, action in data["policy"]}


def evaluate(include_shared=False):
    case = load(MALI / "case.json")
    sources = {
        "mali": MALI / "evidence/metrics.json",
        "first": HERE / "evidence/offer-policy/results.json",
        "refit": HERE / "evidence/offer-refit/results.json",
    }
    observed = load(sources["mali"])
    scopes = observed["published_scope_candidates"]["whole_set"]
    labels = [p["id"] for p in case["options"]]
    menus = {"france-overlap": "AEG", "france-impasse": "AG", "russia": "CE"}
    totals, traces = Counter(), {}
    first, second = (freeze_table(load(sources[key])) for key in ("first", "refit"))
    arms = (
        ("verify_first", "verify_first", {}), ("offer_first", "offer_first", {}),
        ("open_offer", "open_offer", {}),
        ("fit", "verify_first", first), ("refit", "open_offer", second),
    )
    if include_shared:
        from offer_abstract import SharedPolicy
        sources["shared"] = HERE / "evidence/offer-abstract/results.json"
        shared = SharedPolicy({(tuple(key[0]), *key[1:]): value
                               for key, value in load(sources["shared"])["policy"]})
        arms += (("shared", "open_offer", shared),)
    for flipped in (False, True):
        layout = {**case, "roles": case["roles"][::-1]} if flipped else case
        order = "flipped" if flipped else "original"
        for variant in ("france-overlap", "france-impasse"):
            cards = ("russia", variant) if flipped else (variant, "russia")
            true = tuple(bits(labels, menus[card]) for card in cards)
            local = []
            for i, card in enumerate(cards):
                signs = observed["package_predictions"][card]
                yes = bits(labels, [k for k in labels if signs[k]["sign"] is True])
                no = bits(labels, [k for k in labels if signs[k]["sign"] is False])
                assert yes & ~true[i] == no & true[i] == 0
                local.append((yes, no))
            scope = tuple(bits(labels, [p["id"] for p in case["options"] if p["scope"] in scopes[card]]) for card in cards)
            expected = "AGREEMENT_POSSIBLE" if variant.endswith("overlap") else "IMPASSE"
            for a, b in product(*(menus[card] for card in cards)):
                row = len(labels), true, tuple(local), (bits(labels, a), 0, bits(labels, b), 0), scope
                for arm, script, policy in arms:
                    result = rollout(layout, row, script, policy)
                    key = order, variant, arm
                    totals[*key, "solved"] += result["decision"]["state"] == expected
                    totals[*key, "slots"] += result["slots"]
                    totals[*key, "checks"] += result["checks"]
                    traces["/".join((*key, a+b))] = result
    for key, episode in observed["paths"].items():
        variant, method, arm, opening = key.split("/")
        if (method, arm) == ("whole_set", "strong"):
            current = traces[f"original/{variant}/verify_first/{opening}"]
            assert current["slots"] == episode["slots"]
            assert current["decision"]["state"] == episode["public"]["state"]
    return {"scope": "Recorded model evidence from one transfer family. Every admitted claim is checked against the fictional authored menu.",
            "inputs": {k: engine.sha256(p.read_bytes()).hexdigest() for k, p in sources.items()},
            "metrics": engine.sp.flatten(totals), "paths": traces}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shared", action="store_true")
    print(json.dumps(evaluate(parser.parse_args().shared), indent=2))
