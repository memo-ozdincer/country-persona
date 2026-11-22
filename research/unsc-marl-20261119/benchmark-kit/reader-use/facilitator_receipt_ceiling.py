"""Enumerate the optimal decentralized policy for frozen chair records."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import facilitator_feedback_cost as prior
import facilitator_typed_clarification_score as compiled

HERE = prior.HERE
EVIDENCE = HERE / "facilitator-quote-order-evidence/results.json"
POLICIES = HERE / "facilitator-feedback-cost-results.json"
base = prior.base
DEV = prior.dev
MODE = "quote"


def datasets():
    rows = list(prior.cases())
    captured = DEV.load(EVIDENCE)
    fresh = captured["clarification"]["relation_first"]
    clarification = []
    for panel, _, _, _, _, _, _, _, _ in compiled.study.prior.source_inputs():
        relations = tuple(fresh["decisions"][f"{panel}/direct"]["relations"])
        for mask, flags in enumerate(product((False, True), repeat=2)):
            seen = frozenset(i for i, present in enumerate(flags) if present)
            address = f"{panel}/direct" if mask == 3 else f"{panel}/direct/mask{mask}"
            row = fresh["review"][f"{address}/bound"]
            assert base.decision(relations, seen) == row["disposition"]
            clarification.append((panel, MODE, seen, relations, row["expected"], row["disposition"], row["strict"]))
    return {"unifil_colombia": prior.record.collect(r[1:] for r in rows if r[0] == "development"),
            "bosnia_afghanistan": prior.record.collect(clarification),
            "abyei_minusca": prior.record.collect(r[1:] for r in rows if r[0] == "transfer")}


def tensor(cases, inventory, feedback):
    roster = base.base.roster(inventory)
    first_index, second_index = {}, {}
    branches = []
    for case in cases.values():
        reads, grades = case["reads"], case["receipts"]
        for (left, right), mass in roster.items():
            first = "first", base.local(left, reads)
            left_id = first_index.setdefault(first, len(first_index))
            for a, card_a in enumerate((*left, base.PASS)):
                for ok, ack, link in base.events(card_a):
                    heard = base.observation(card_a, reads, ack and feedback)
                    second = "second", base.local(right, reads, heard)
                    right_id = second_index.setdefault(second, len(second_index))
                    for b, card_b in enumerate((*right, base.PASS)):
                        net = -base.paid(card_a, card_b)
                        for received, probability in ((True, base.base.CHAIR), (False, 1 - base.base.CHAIR)):
                            mask = base.delivered(card_a, ok, card_b, received)
                            net += probability * prior.record.rewards(grades[mask])[1]
                        branches.append((left_id, a, right_id, b, mass * link * net / len(cases)))
    payoff = np.zeros((len(first_index), 3, len(second_index), 3))
    for row in branches:
        payoff[row[:4]] += row[4]
    return first_index, second_index, payoff


def enumerate_first(payoff):
    """Fix one first-desk table. The second desk's best choice separates by state."""
    states = payoff.shape[0]
    tables = 3 ** states
    assert tables <= 3 ** 14, "Use a bounded exact solver for a larger state space"
    powers = 3 ** np.arange(states)
    best = -np.inf
    left = right = None
    for start in range(0, tables, 2048):
        ids = np.arange(start, min(tables, start + 2048))
        actions = (ids[:, None] // powers) % 3
        returns = np.zeros((len(ids), *payoff.shape[2:]))
        for s in range(states):
            returns += payoff[s, actions[:, s]]
        expected = returns.max(axis=2).sum(axis=1)
        row = int(expected.argmax())
        if expected[row] > best:
            best = float(expected[row])
            left = actions[row]
            right = returns[row].argmax(axis=1)
    return best, left, right, tables


def solve(cases, inventory, feedback):
    first, second, grid = tensor(cases, inventory, feedback)
    optimum, left, right, evaluated = enumerate_first(grid)
    out = {state: np.eye(3)[actions[index]].tolist()
           for lookup, actions in ((first, left), (second, right)) for state, index in lookup.items()}
    return out, {"exact_net": optimum, "first_states": len(first), "second_states": len(second),
                 "first_tables_enumerated": evaluated}


def stock():
    frozen = DEV.transfer.policy(DEV.transfer.FROZEN)
    independent = {compiled.freeze(row["state"]): row["probabilities"]
                   for row in DEV.load(POLICIES)["independent_policy"]}
    return frozen, independent


def measure(cases, policies, inventory):
    with patch.object(prior.record, "MODES", (MODE,)):
        return prior.record.evaluate(cases, policies, inventory)


def run():
    panels = datasets()
    frozen, independent = stock()
    evidence = {}
    for panel, cases in panels.items():
        assert len(cases) == 4
        evidence[panel] = {}
        for inventory in ("split", "overlap"):
            with_ack, ack_certificate = solve(cases, inventory, True)
            without_ack, no_ack_certificate = solve(cases, inventory, False)
            policies = (("opt_adaptive", "learned", with_ack), ("opt_independent", "learned_erased", without_ack),
                        ("frozen_adaptive", "learned", frozen), ("frozen_erased", "learned_erased", frozen),
                        ("trained_independent", "learned_erased", independent),
                        ("greedy", "greedy", {}), ("greedy_independent", "greedy_erased", {}))
            metrics = measure(cases, policies, inventory)
            bounds = {"opt_adaptive": ack_certificate, "opt_independent": no_ack_certificate}
            for method, certificate in bounds.items():
                assert abs(metrics[method]["summary"][MODE]["brief_net"] - certificate["exact_net"]) < 1e-9
            assert ack_certificate["exact_net"] + 1e-9 >= no_ack_certificate["exact_net"]
            for name, method, _ in policies:
                value = metrics[name]["summary"][MODE]["brief_net"]
                upper = "opt_independent" if method.endswith("erased") else "opt_adaptive"
                assert value <= bounds[upper]["exact_net"] + 1e-9
            evidence[panel][inventory] = {"ceiling": bounds, "results": metrics,
                                         "optimal_policies": {
                                             k: [{"state": state, "probabilities": p} for state, p in policy.items()]
                                             for k, policy in (("adaptive", with_ack), ("independent", without_ack))}}
    rep = DEV.load(EVIDENCE)
    for roster in ("split", "overlap"):
        measured = evidence["bosnia_afghanistan"][roster]["results"]["frozen_adaptive"]["summary"][MODE]["brief_net"]
        earlier = rep["clarification"]["relation_first"]["simulated_delivery"][roster]["frozen"]["summary"]["direct"]["brief_net"]
        assert abs(measured - earlier) < 1e-9
    inputs = (Path(__file__), EVIDENCE, POLICIES, Path(prior.__file__), Path(prior.record.__file__))
    return {"scope": "Exact retrospective benchmark ceilings for two decentralized desks on previously scored records. "
                     "The solver may use the evaluated payoff distribution to choose tables. The actors see only their "
                     "local state and any delivered acknowledgment. This is not a holdout policy fit.",
            "send_fee": base.FEE, "ack_fee": 0.0,
            "input_sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in inputs}, "evidence": evidence}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
