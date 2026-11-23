"""Test whether knowing the remaining speech schedule improves workshop training."""

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

import train_mandates as core


TRAIN_CAPS = (5, 7, 9, 12)
HELD_CAPS = (6, 9, 12)
HELD_SEED = core.SEED + 90
REFERENCE = core.HERE.parents[1] / "reports/council-workshop-mandate-training-20261123/results.json"
CONTEXT = ("closes_now", "can_finish_draft_after_action", "can_finish_certificate_after_action",
           "remaining_cycles")


def budget_features(rows, public, seat, upcoming, seats):
    accepted = set(public["accepted"])
    options = public["options"]
    excluded = set(public["exclusions"])
    current = next(label for label, text in options.items() if text == public["draft"])
    still_due = set(seats) - accepted
    future = set(upcoming)
    results = []
    for kind, label in rows:
        pending = set(seats) if kind == "propose" else still_due - ({seat} if kind == "accept" else set())
        selected = label if kind == "propose" else current
        new_exclusions = excluded | ({label} if kind == "rule_out" else set())
        meeting_continues = kind not in {"declare_impasse", "walk_away"}
        can_finish = meeting_continues and selected not in new_exclusions and pending <= future
        can_certify = kind == "declare_impasse" or (
            meeting_continues and len(options)-len(new_exclusions)+1 <= len(upcoming))
        results.append((float(kind == "accept" and not pending), float(can_finish),
                        float(can_certify), len(upcoming)/len(seats)))
    return results


def greedy(weights):
    def choose(rows, selected, public, seat, feats):
        probabilities = core.policy(rows, feats, weights)
        index = max(range(len(rows)), key=probabilities.__getitem__)
        return rows[index], None
    return choose


def close_first(rows, selected, public, seat, feats):
    # Complete an eligible last signature before gathering optional exclusions.
    accept = rows.index(("accept", selected))
    if selected not in public["exclusions"] and feats[accept][1] and feats[accept][len(core.FEATURES)]:
        return ("accept", selected), None
    return core.scripted(rows, selected, public, seat), None


def compare(cohorts, policies):
    summary, traces = {}, {}
    for cap in HELD_CAPS:
        cap_key = str(cap)
        summary[cap_key], traces[cap_key] = {}, {}
        for name, instances in cohorts.items():
            totals = {label: {"feasible": Counter(), "infeasible": Counter()} for label in policies}
            traces[cap_key][name] = []
            for i, instance in enumerate(instances):
                row = {"index": i, "policies": {}}
                for label, (choose, context) in policies.items():
                    result, _ = core.rollout(instance, choose, turn_cap=cap, context=context)
                    row["policies"][label] = result
                    group = "feasible" if result["feasible_packages"] else "infeasible"
                    totals[label][group][result["outcome"]] += 1
                    totals[label][group]["speeches"] += result["turns"]
                traces[cap_key][name].append(row)
            summary[cap_key][name] = {label: {group: dict(sorted(values.items())) for group, values in groups.items()}
                                      for label, groups in totals.items()}
    return summary, traces


def run():
    train_pools, held = core.pools()
    reference = json.loads(REFERENCE.read_text())["fits"]["verified"]["weights"]
    blind = core.train(train_pools, "verified", turn_caps=TRAIN_CAPS)
    aware = core.train(train_pools, "verified", turn_caps=TRAIN_CAPS, context=budget_features,
                       extra_width=len(CONTEXT))
    policies = {
        "prior_nine_speeches": (greedy(reference), None),
        "variable_budget_blind": (greedy(blind["weights"]), None),
        "variable_budget_aware": (greedy(aware["weights"]), budget_features),
        "checked_script_with_closure": (close_first, budget_features),
    }
    summary, traces = compare(core.held_worlds(held, HELD_SEED), policies)
    paths = (Path(__file__), Path(core.__file__), REFERENCE,
             core.HERE/"meeting.py", core.HERE/"mandates.py")
    return {"plan": {"train_caps": TRAIN_CAPS, "held_caps": HELD_CAPS, "held_seed": HELD_SEED,
                     "training_episodes_per_arm": core.TRAIN_EPISODES, "budget_features": CONTEXT,
                     "pins": {str(p.relative_to(core.HERE.parents[1])): sha256(p.read_bytes()).hexdigest()
                              for p in paths}},
            "training": {"variable_budget_blind": blind, "variable_budget_aware": aware},
            "held": summary, "outcomes": traces}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
