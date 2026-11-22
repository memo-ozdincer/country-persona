"""Replay model disclosures with a learned relay and score error propagation."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import torch

import relay_compromise_joint as joint
import relay_compromise_language as language
from relay_compromise_audit import oracle
from relay_compromise_completions import FIT
from relay_ranked_mandates import inputs, order


def match(options, filters):
    def fits(package, conditions):
        return all(package[name] == value for name, value in conditions.items())
    return tuple(next((grade for grade, cond in filters if fits(package, cond)), 0) for package in options)


def authored_check(tasks):
    # Manual structured annotation of the source mandate clauses. Keep it
    # separate from both the model prompt and the cards keyed in the simulator.
    v1 = {"scope": "staged", "coordination": "joint", "explicit_consent": True}
    v2 = {**v1, "coordination": "un"}
    v3 = {**v1, "scope": "broad"}
    v4 = {**v1, "scope": "focused", "coordination": "host"}
    v5 = {**v4, "coordination": "joint"}
    s1 = {"scope": "focused", "instrument": "study", "forum": "disarmament"}
    s2 = {**s1, "scope": "staged"}
    s3 = {**s2, "instrument": "negotiation"}
    s4 = {**s3, "scope": "broad", "review": True}
    s5 = {**s4, "forum": "council", "review": False}
    fields = (
        (((v1, v2, v3), (v3, v2, v1), (v4, v5, None)),
         ((v2, None, v1), (v1, None, v2), (v5, v4, None))),
        (((s2, s1, s3), (s3, s2, s1), (s4, s5, None)),
         ((s2, s3, s1), (s1, s3, s2), (s5, s4, None))),
    )
    for (name, task), rule, source in zip(tasks.items(), fields, language.ranked.FILES, strict=True):
        options = json.loads(source.read_text())["options"]
        for seat, profiles in enumerate(rule):
            for index, profile in enumerate(profiles):
                filters = [(grade, conditions) for grade, conditions in zip((3, 2, 1), profile, strict=True)
                           if conditions is not None]
                assert match(options, filters) == task.cards[seat][index], (name, seat, index)


def best_outputs(directory, locked_inputs):
    with locked_inputs():
        prompts = language.scorer.read(directory)
    scores = {}
    for (name, role, identity, rotation, _), row in sorted(prompts.items()):
        winner = max(range(4), key=row["scores"].__getitem__)
        prediction = order(rotation)[winner] if winner < 3 else None
        scores[name, role, identity, rotation] = {"predicted": prediction, "correct": prediction == identity,
                                                    "legal_mass": row["legal_mass"],
                                                    "scores": row["scores"]}
    return scores


def readout(table, policy, task, left, right):
    choices = []
    for a, b in task.completions(left, right):
        f, frozen, menu = table[task.name, 3, a, b, False]
        logits = policy.rank(f, frozen)
        choices.append(menu[int(logits.argmax())])
    return choices[0] if len(set(choices)) == 1 else "unresolved"


def answered(task, left, right):
    actions = set.intersection(*(oracle(task.actions[:-1], task.card(0, a), task.card(1, b))
                                 for a, b in task.completions(left, right)))
    return actions or {"unresolved"}


def corroborated_grades(task, actual, delivered):
    observations = []
    domains = []
    for role, (truth_id, claimed_id) in enumerate(zip(actual, delivered, strict=True)):
        truth = task.card(role, truth_id)
        claim = task.card(role, claimed_id)
        verified = {i: grade for i, (grade, claimed) in enumerate(zip(truth, claim, strict=True))
                    if claimed_id and grade == claimed}
        observations.append({task.actions[i]: grade for i, grade in verified.items()})
        domains.append([card for card in task.cards[role] if all(card[i] == grade for i, grade in verified.items())])
    warranted = set.intersection(*(oracle(task.actions[:-1], a, b) for a, b in product(*domains)))
    return observations, warranted or {"unresolved"}


def replay(tasks, scores):
    fit = json.loads(FIT.read_text())
    assert fit["inputs_sha256"] == sha256((joint.SOURCE / "actions.jsonl").read_bytes()).hexdigest()
    policy = joint.Joint(True)
    policy.load_state_dict({key: torch.tensor(value) for key, value in fit["training"]["qwen_joint"]["state"].items()})
    table = joint.unpack()
    all_results = {}
    with torch.no_grad():
        for family, task in tasks.items():
            worlds = []
            for i, j in product(range(3), repeat=2):
                exact = (task.first[i], task.second[j])
                layouts = tuple(tuple(scores[family, role, code, rotation]["predicted"]
                                      for rotation in range(2))
                                for role, code in enumerate((i, j)))
                inputs_by_arm = {
                    "first_order": tuple(s[0] for s in layouts),
                    "rotated": tuple(s[1] for s in layouts),
                    "layout_consensus": tuple(s[0] if s[0] == s[1] else None for s in layouts),
                    "truthful_control": (i, j),
                }
                results = {}
                for arm, submitted in inputs_by_arm.items():
                    card_domains = (task.first, task.second)
                    sent = tuple(card_domains[r][ind] if ind is not None else 0 for r, ind in enumerate(submitted))
                    trace = joint.routed(task, policy, sent, "peer")
                    delivered = language.ranked.delivered(trace)
                    verified = tuple(a if a == e else 0 for a, e in zip(delivered, exact, strict=True))
                    actual = answered(task, *exact)
                    plaintext_warrant = answered(task, *delivered)
                    truth_warrant = answered(task, *verified)
                    prediction = readout(table, policy, task, *delivered)
                    checked_after_reject = readout(table, policy, task, *verified)
                    grade_receipts, grade_warrant = corroborated_grades(task, exact, delivered)
                    results[arm] = {"submitted_cards": sent, "delivered": delivered, "after_truth_rejection": verified,
                                    "choice": prediction, "status_on_claimed_cards": sorted(plaintext_warrant),
                                    "warrant_on_verified_cards": sorted(truth_warrant),
                                    "oracle_grade_receipts": grade_receipts,
                                    "warrant_on_verified_grades": sorted(grade_warrant),
                                    "choice_after_truth_rejection": checked_after_reject,
                                    "correct_actual": prediction in actual,
                                    "warranted_verified": prediction in truth_warrant,
                                    "after_reject_warranted": checked_after_reject in truth_warrant,
                                    "false_received_cards": sum(bool(a) and a != e for a, e in zip(delivered, exact, strict=True)),
                                    "turns": trace["deliveries"]}
                worlds.append({"world": exact, "optima": sorted(answered(task, *exact)), "arms": results})
            all_results[family] = worlds
    return all_results


def audit(directory, locked_inputs=inputs):
    torch.set_num_threads(1)
    tasks = language.ranked.fixtures()
    authored_check(tasks)
    scores = best_outputs(directory, locked_inputs)
    records = [{"family": name, "role": role, "profile_index": identity, "menu_rotation": rotation, **row}
               for (name, role, identity, rotation), row in scores.items()]
    return {"source_sha256": sha256((directory/"actions.jsonl").read_bytes()).hexdigest(),
            "authored_mandate_match_checks": 12,
            "disclosures": records,
            "routes": replay(tasks, scores)}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    cli.add_argument("--grounded", action="store_true")
    args = cli.parse_args()
    locked = inputs
    if args.grounded:
        from relay_ranked_mandates_grounded import inputs as locked
    print(json.dumps(audit(args.directory, locked), indent=2))
