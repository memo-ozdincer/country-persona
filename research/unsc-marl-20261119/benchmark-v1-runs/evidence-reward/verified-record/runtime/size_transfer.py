"""Exhaustive three-option transfer using frozen four-option policies."""
from collections import Counter
from functools import cache
from itertools import combinations, product
import json
from pathlib import Path

import numpy as np

import workshop as w

VALUES = (.8, 1.)
HERE = Path(__file__).resolve().parent


def evaluate(menu, state, target):
    decision, credit = w.g.terminal(menu, state)
    assert decision in ("UNRESOLVED", target)
    return credit, decision == target, credit == 1.


def metrics(menu, state_score, rates, cap, team):
    witnesses = []
    for truth in w.g.WORLDS:
        target = w.g.terminal(menu, truth)[0]
        values = w.score.expected(menu, state_score, rates, truth, cap, *team)
        witnesses.append((target, values))
    matrix = np.stack([d for _, d in witnesses])
    points, accuracy, _, queries, attempts = map(float, matrix.mean(axis=0))
    return {"net": points - w.fit.core.QUERY_COST * queries - w.fit.core.SEND_COST * attempts,
            "accuracy": accuracy, "queries": queries, "attempts": attempts,
            "agreement_recall": float(np.mean([d[1] for target, d in witnesses if target != "IMPASSE"])),
            "impasse_recall": float(np.mean([d[1] for target, d in witnesses if target == "IMPASSE"]))}


def run():
    heads, _ = w.loaded()
    report = {}
    for menu in combinations(w.g.WORLDS, 3):
        rows = {}

        @cache
        def credit(state, gold):
            return evaluate(menu, state, gold)

        for (profile, rates), cap in product(w.PROFILES.items(), (2, 3)):
            candidates = w.teams(menu, rates, VALUES, heads)
            selected = {k: metrics(menu, credit, rates, cap, candidates[k])
                        for k in ("former", "aware", "fixed", "silent")}
            best = max(("former", "aware", "silent"),
                       key=lambda k: (selected[k]["net"], k == "silent"))
            exact = w.fit.exact(menu, rates, cap, VALUES)
            assert all(d["net"] < exact + 1e-10 for d in selected.values())
            rows[f"{profile}/{cap}"] = selected | {"chosen": best, "exact_net": exact}
        report["-".join("".join(map(str, x)) for x in menu)] = rows
    keys = tuple(next(iter(report.values())))
    summary = {}
    for condition in keys:
        rows = [item[condition] for item in report.values()]
        selected = [row[row["chosen"]]["net"] for row in rows]
        summary[condition] = {
            "mean": {k: float(np.mean([row[k]["net"] for row in rows]))
                     for k in ("former", "aware", "fixed", "silent")},
            "selected_mean_net": float(np.mean(selected)),
            "exact_mean_net": float(np.mean([row["exact_net"] for row in rows])),
            "selected_teams": Counter(row["chosen"] for row in rows),
            "negative_menu_counts": {k: sum(row[k]["net"] < -1e-10 for row in rows)
                                     for k in ("former", "aware", "fixed")},
            "selector_loses_to_fixed": sum(v < row["fixed"]["net"] - 1e-10
                                           for v, row in zip(selected, rows, strict=True)),
            "maximum_selector_regret": max(row["exact_net"] - value
                                           for row, value in zip(rows, selected, strict=True)),
        }
    return {"menus": len(report), "conditions": sum(len(v) for v in report.values()),
            "summary": summary, "menus_detail": report}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
