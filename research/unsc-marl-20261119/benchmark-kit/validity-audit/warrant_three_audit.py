"""Independently verify the held disclosure trajectories and issued certificates."""
import argparse
from functools import lru_cache
from itertools import product
import json
from pathlib import Path

import numpy as np

import warrant_three as study


def validate(task, table, prior):
    possible = list(product(*task.cards.tolist()))

    @lru_cache(maxsize=None)
    def allowed(reports):
        worlds = [world for world in possible if all(world[role][slot] == grade for role, slot, grade in reports)]
        feasible_winners = []
        for world in worlds:
            eligible = [(min(col), sum(col), i) for i, col in enumerate(zip(*world, strict=True)) if all(col)]
            maximum = max(((m, t) for m, t, _ in eligible), default=None)
            feasible_winners.append({i for m, t, i in eligible if (m, t) == maximum} or {3})
        result = set.intersection(*feasible_winners)
        return 2 if result == {3} else int(bool(result))

    request = task.requests(task.weights(np.eye(3)[table], prior))
    recommend = impasse = requests = 0.
    distinct = set()
    for idx, (types, truth) in enumerate(zip(study.TYPES, possible, strict=True)):
        sends = table[np.arange(3), types]
        s = int(sends @ np.array([9, 3, 1]))
        for loss_id, flags in enumerate(study.LINKS):
            evidence = tuple((i, int(slot), truth[i][slot]) for i, slot in enumerate(sends) if flags[i])
            distinct.add(evidence)
            first = allowed(evidence)
            action = request[task.state[idx, s, loss_id]]
            mass = prior[idx] * study.P_LINKS[loss_id]
            if action:
                role, slot = study.ACTIONS[action]
                assert (role, slot) not in {fact[:2] for fact in evidence}
                second = allowed((*evidence, (role, slot, truth[role][slot])))
                receive = study.two.REPLY_DELIVERY
                requests += mass
            else:
                second, receive = first, 0.
            recommend += mass * ((1 - receive) * (first == 1) + receive * (second == 1))
            impasse += mass * ((1 - receive) * (first == 2) + receive * (second == 2))
    net = recommend + impasse - study.two.REPLY_COST * requests
    return {"net": float(net), "recommend": float(recommend), "impasse": float(impasse),
            "requests": float(requests), "distinct_opening_views": len(distinct)}


def run(data):
    checks = []
    for entry in data["results"]:
        task = study.Workshop(np.asarray(entry["cards"]))
        for label, observed in entry["priors"].items():
            expected = observed["arms"]["fitted"]
            exact = validate(task, np.asarray(expected["opening_table"]), study.prior(label == "correlated"))
            assert all(abs(expected[k] - exact[k]) < 1e-12 for k in ("net", "recommend", "impasse", "requests"))
            checks.append({"domain": entry["i"], "prior": label, **exact})
    return {"verified_conditions": len(checks), "opening_branches_per_condition": 512, "checks": checks}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("report", type=Path)
    print(json.dumps(run(json.loads(cli.parse_args().report.read_text())), indent=2))
