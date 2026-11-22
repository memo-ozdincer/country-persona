"""Audit baseline-relative results and confirm the lower bound by direct tables."""
import argparse
from itertools import product
import json
from pathlib import Path

import numpy as np

import warrant_request_safety as fit


def exact_bound(task, p, history, current, action, baseline):
    ledger, compatible = fit.interface.receiver.flexible.registry(task)
    each = [[], [], []]
    for role in range(3):
        for model in fit.COMPATIBLE_TABLES:
            retain = True
            for seen in history:
                slot = ledger[seen, role]
                if slot < 0:
                    continue
                matches_grade = np.unique(fit.world.TYPES[compatible[seen], role])
                if not any(model[typ] == slot for typ in matches_grade):
                    retain = False
                    break
            if retain:
                each[role].append(model)
    state_slots = ledger[current]
    true_returns = {}
    for w in range(64):
        positions = np.argwhere(task.state[w] == current)
        if len(positions):
            values = [task.pay[w, s, loss] for s, loss in positions]
            assert all(np.array_equal(values[0], v) for v in values)
            true_returns[w] = values[0][action] - values[0][baseline]
    possible = []
    for a, b, c in product(*each):
        marginal = []
        for w, card_types in enumerate(fit.world.TYPES):
            if not compatible[current, w]:
                continue
            if all(slot < 0 or plan[card_types[role]] == slot
                   for role, (slot, plan) in enumerate(zip(state_slots, (a, b, c), strict=True))):
                marginal.append(w)
        if marginal:
            scale = sum(p[w] for w in marginal)
            possible.append(sum(p[w] * true_returns[w] for w in marginal) / scale)
    return min(possible)


def audit_archived(data):
    checked = 0
    for record in data["language"]:
        base = record["scores"]["grade_only"]["mean_net"]
        for n in fit.PREFIXES:
            score = record["scores"][str(n)]
            assert score["negative_histories"] == 0
            assert score["mean_net"] >= base + score["mean_lower_gain_bound"] - 1e-12
            checked += 1
    for record in data["synthetic"]:
        for team in ("mixed", "coordinate"):
            base = record["scores"][team]["grade_only"]["mean_net"]
            for n in fit.PREFIXES:
                score = record["scores"][team][str(n)]
                assert score["negative_histories"] == 0
                assert score["mean_net"] >= base + score["mean_lower_gain_bound"] - 1e-12
                checked += 1
    return checked


def verify_example():
    record = json.loads(fit.LANGUAGE.read_text())["replay"]["domains"][1]
    p = fit.world.prior(False)
    task = fit.world.Workshop(np.asarray(record["cards"]))
    planner = fit.Planner(task, p)
    _, occurrence = fit.interface.actual_values(task, p, np.asarray(record["admitted_slots"]))
    gen = np.random.default_rng(123)
    for _ in range(16):
        history = np.searchsorted(np.cumsum(occurrence), gen.random(16), side="right")
        support = planner.table_support(history)
        if np.prod([len(s) for s in support]) > 1500:
            continue
        for state in np.flatnonzero(occurrence):
            q, credited = planner.decision(int(state), support)
            if credited > 0.:
                explicit = exact_bound(task, p, history, state, q, planner.baseline[state])
                assert abs(credited - explicit) < 1e-12
                return {"certificate_state": int(state), "baseline_request": int(planner.baseline[state]),
                        "adaptive_request": int(q), "lower_bound": explicit,
                        "surviving_tables_per_role": list(map(len, support))}
    raise AssertionError("No informative audit example")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("report", type=Path)
    data = json.loads(cli.parse_args().report.read_text())
    print(json.dumps({"verified_stable_condition_prefixes": audit_archived(data), "direct_check": verify_example()},
                     indent=2))
