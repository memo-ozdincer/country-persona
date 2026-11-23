"""Audit the trained policies against production transitions and exact bounds."""

import json
from collections import Counter
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "research/council_workshop"))

import train_mandates as train
from meeting import FLOOR
from run import simulate


def best_possible(instance):
    seats, draft, mandates = instance
    feasible = set(mandates.options).intersection(*mandates.allowed.values())
    if feasible:
        return len(seats) + (draft not in {mandates.options[label] for label in feasible})
    menu = frozenset(mandates.options)
    reachable = {frozenset()}
    for step in range(1, train.TURN_CAP + 1):
        if menu in reachable:
            return step
        seat = seats[(step-1) % len(seats)]
        reachable |= {seen | {label} for seen in reachable for label in menu-mandates.allowed[seat]}
    return None


def greedy(weights):
    def choose(rows, selected, public, seat, feats):
        p = train.policy(rows, feats, weights)
        return rows[max(range(len(p)), key=p.__getitem__)], None

    return choose


def production(instance, choose):
    seats, draft, rules = instance
    case = {"title": "Fictional packages", "brief": "Synthetic verification",
            "source": "Synthetic verification", "draft": draft,
            "delegations": {seat: ["Use your private fictional mandate."] for seat in seats},
            "mandate_game": {"options": rules.options, "allowed": {s: sorted(rules.allowed[s]) for s in seats}}}

    def decide(seat, prompt, schema):
        packet = json.JSONDecoder().raw_decode(prompt[prompt.index("{"):])[0]
        public = packet["public"]
        if schema == FLOOR:
            last = public["history"][-1]["country"]
            return {"action": "request_floor" if seat == seats[(seats.index(last)+1) % len(seats)] else "pass"}
        allowed = packet["private_mandate"]["allowed_packages"]
        assert frozenset(allowed) == rules.allowed[seat] and set(packet["evidence"]) == {seat}
        rows, current = train.candidates(public, seat, allowed)
        feats = train.features(rows, current, public, seat, allowed, len(seats))
        (kind, label), _ = choose(rows, current, public, seat, feats)
        return {"action": kind, "version": public["version"],
                "text": label if kind in {"propose", "rule_out"} else kind}

    result = simulate(case, seats, "meeting", train.TURN_CAP, False, decide, 50)
    return result["mandate_score"] | {"status": result["status"], "turns": len(result["history"])}


def private_contrasts(choose):
    outcomes = Counter()
    labels = ["one", "two", "three"]
    for current in labels:
        alternatives = [label for label in labels if label != current]
        public = {"options": {label: label for label in labels}, "draft": current,
                  "accepted": ["B","C","D","E"], "exclusions": {}}
        for prior in ([alternatives[0]], [alternatives[1]], alternatives):
            actions = []
            for allowed in (prior, prior+[current]):
                rows, selected = train.candidates(public, "A", allowed)
                feats = train.features(rows, selected, public, "A", allowed, 5)
                actions.append(choose(rows, selected, public, "A", feats)[0][0])
            outcomes["contrast_pairs"] += 1
            outcomes["avoids_invalid_accept"] += actions[0] != "accept"
            outcomes["accepts_allowed"] += actions[1] == "accept"
            outcomes["passes_both"] += actions[0] != "accept" and actions[1] == "accept"
    return dict(outcomes)


def current_first(rows, selected, public, seat, feats):
    remaining = public["options"].keys() - public["exclusions"].keys()
    if ("declare_impasse", selected) in rows:
        return ("declare_impasse", selected), None
    if ("rule_out", selected) in rows:
        return ("rule_out", selected), None
    if selected in remaining and seat not in public["accepted"]:
        return ("accept", selected), None
    if selected not in remaining:
        alternatives = [row for row, inputs in zip(rows, feats, strict=True)
                        if row[0] == "propose" and row[1] in remaining and inputs[1]]
        if alternatives:
            return alternatives[0], None
    return train.scripted(rows, selected, public, seat), None


def run():
    result = json.loads((HERE/"results.json").read_text())
    _, held = train.pools()
    cohorts = train.held_worlds(held)
    checks = 0
    analyses = {}
    policies = {name: greedy(fit["weights"]) for name, fit in result["fits"].items()}
    policies["current_first_rule"] = current_first
    for name, choose in policies.items():
        analyses[name] = {"private_contrasts": private_contrasts(choose), "cohorts": {}}
        for cohort, instances in cohorts.items():
            reasons = Counter()
            for instance in instances:
                fast, _ = train.rollout(instance, choose)
                assert fast == production(instance, choose)
                lower = best_possible(instance)
                if fast["reward"]:
                    assert lower is not None and lower <= fast["turns"]
                    reasons[fast["outcome"]] += 1
                elif lower is None:
                    reasons["unachievable_under_cap"] += 1
                else:
                    reasons["miss_with_oracle_headroom"] += 1
                checks += 1
            analyses[name]["cohorts"][cohort] = dict(reasons)
    return {"production_episodes_replayed": checks, "analyses": analyses}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
