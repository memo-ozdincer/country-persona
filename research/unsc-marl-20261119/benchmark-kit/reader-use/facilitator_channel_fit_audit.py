"""Independently enumerate inventories and losses for the robust tail."""
import argparse
from itertools import product
import json
from pathlib import Path

import numpy as np

import facilitator_channel_fit as study


def enumerate_receipts(opener, tail, prior, admission):
    left, right = opener
    requests, replies = tail
    mass, cost, queries = np.zeros(8), 0., 0.
    for l, r in product(range(8), repeat=2):
        x, y = left[l], right[r]
        for links in product((0, 1), repeat=4):
            a, b, heard, delivered = links
            weight = prior[l, r] * (1 - study.D.LOSS) ** sum(links) * study.D.LOSS ** (4 - sum(links))
            mask = int(study.ROUTE.BITS[x] * a | study.ROUTE.BITS[y] * b)
            q = requests[mask]
            t = q * heard
            c = replies[r, y, t]
            admitted = admission[t, c] * delivered
            mass[mask] += weight * (1 - admitted)
            mass[mask | study.ROUTE.BITS[c]] += weight * admitted
            cost += weight * (study.D.SEND_COST[x] + study.D.SEND_COST[y] + study.D.QUERY_COST[q] + study.D.SEND_COST[c])
            queries += weight * (q != 0)
    return mass, cost, queries


def audit(report):
    banks = study.OLD.base.cases()[1]
    banks["resolution_2593"] = (study.live.rubric(), study.live.rubric())
    measured = np.asarray(report["measured_admission"])
    checked, active = 0, []
    for name, (public, points) in banks.items():
        regimes = {"source_only": study.PERFECT, "question_visible": measured} if name == "resolution_2593" else study.STRESS
        for label in study.live.PRIORS:
            prior = study.ROUTE.TEST_PRIORS[label]
            opener, opening = study.context(public, prior)
            for regime, actual in regimes.items():
                estimate = study.PERFECT if actual is study.PERFECT else study.DESIGN
                tail = study.action_policy(report["robust"], public, opening, estimate)
                mass, cost, queries = enumerate_receipts(opener, tail, prior, actual)
                observed = report["results"][name][label][regime]["robust_fit"]
                assert np.allclose(mass, observed["receipt_mass"], atol=1e-12, rtol=0)
                assert abs(cost - observed["cost"]) < 1e-12
                assert abs(mass @ study.OLD.base.terminal(points) - cost - observed["net"]) < 1e-12
                if queries > 1e-12:
                    active.append({"family": name, "prior": label, "regime": regime, "expected_requests": queries})
                checked += 1
    return {"checked_policy_cells": checked, "nonzero_request_cells": active, "events_per_cell": 1024}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("report", type=Path)
    print(json.dumps(audit(json.loads(cli.parse_args().report.read_text())), indent=2))
