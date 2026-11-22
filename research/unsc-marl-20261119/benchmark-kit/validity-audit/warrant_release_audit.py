"""Replay the fitted releases with an independently constructed receipt ledger."""
import argparse
from collections import defaultdict
from itertools import product
import json
from pathlib import Path

import numpy as np

from check import warrant, winners
import trained_warrant as fit


def audit_panel(roles, p, weights):
    world = list(product(*roles))
    env = fit.environment(roles, p)
    forecast = fit.features(roles, env)
    opening = [(f * w).sum(-1).argmax(1) for f, w in zip(forecast, weights, strict=True)]

    def permissible(facts):
        options = [winners(fit.MENU, cards, "full") for cards in world
                   if all(cards[side][slot] == grade for side, slot, grade in facts)]
        return warrant(options)

    opportunities = defaultdict(list)
    for l, r in product(range(4), repeat=2):
        cards = roles[0][l], roles[1][r]
        moves = int(opening[0][l]), int(opening[1][r])
        for links in product((False, True), repeat=2):
            facts = tuple((i, moves[i], cards[i][moves[i]]) for i in range(2) if links[i])
            mass = p[l, r] * np.prod([1 - fit.LOSS if x else fit.LOSS for x in links])
            opportunities[facts].append((cards, mass))

    net, observed_branch_count = 0., 0
    examples = {}
    for facts, branches in opportunities.items():
        onset = permissible(facts)
        before = int(onset != {"unresolved"})
        alternatives = {None: (sum(mass for _, mass in branches) * before, None)}
        for side, slot in product(range(2), range(3)):
            if any(f[:2] == (side, slot) for f in facts):
                continue
            value = 0.
            resolved = None
            for cards, mass in branches:
                evidence = (*facts, (side, slot, cards[side][slot]))
                after = permissible(evidence)
                if after != {"unresolved"}:
                    assert after <= winners(fit.MENU, cards, "full")
                    if not before:
                        resolved = {"opening_facts": facts, "request": [side, slot], "reply_grade": cards[side][slot],
                                    "initially_warranted": sorted(onset), "after_reply": sorted(after)}
                value += mass * ((1 - fit.REPLY_DELIVERY) * before + fit.REPLY_DELIVERY *
                                 (after != {"unresolved"}) - fit.REPLY_COST)
            alternatives[(side, slot)] = (value, resolved)
        choice, (value, example) = max(alternatives.items(), key=lambda option: option[1][0])
        if choice is not None and example:
            examples.setdefault("request_resolved", example)
        net += value
        for cards, _ in branches:
            if before:
                assert onset <= winners(fit.MENU, cards, "full")
            observed_branch_count += 1
    return float(net), observed_branch_count, examples


def run(results):
    weights = np.asarray(results["fit"])
    audited = []
    for name, domain in fit.PANELS.items():
        for label, correlated in (("uniform", False), ("correlated", True)):
            for row in results["results"][name][label]:
                order = row["order"]
                roles = tuple(tuple(tuple(card[i] for i in order) for card in side) for side in domain)
                net, count, examples = audit_panel(roles, fit.prior(correlated), weights)
                assert abs(row["arms"]["fit"]["net"] - net) < 1e-12
                audited.append({"panel": name, "prior": label, "order": order, "net": net,
                                "opening_branches": count, "examples": examples})
    return {"policy_cells": len(audited), "false_certifications": 0, "records": audited}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("report", type=Path)
    print(json.dumps(run(json.loads(cli.parse_args().report.read_text())), indent=2))
