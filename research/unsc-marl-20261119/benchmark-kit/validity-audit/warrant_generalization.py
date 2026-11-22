"""Check the frozen workshop policy on unfiltered, separately drawn domains."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

import trained_warrant as study

SEED = 25931
COUNT = 32


def orbit(domain):
    return {tuple(tuple(sorted(tuple(card[i] for i in order) for card in side)) for side in domain)
            for order in study.ORDERINGS}


def generate():
    fit_orbits = set.union(*(orbit(case) for case in (*study.training_domains(), *study.PANELS.values())))
    seen = set()
    rng = np.random.default_rng(SEED)
    for i in range(COUNT):
        pair = []
        for _ in range(2):
            ids = rng.choice(64, size=4, replace=False)
            pair.append(tuple((int(k // 16), int(k // 4 % 4), int(k % 4)) for k in ids))
        domain = tuple(pair)
        signature = orbit(domain)
        assert not signature & (fit_orbits | seen)
        seen |= signature
        yield i, domain


def evaluate(path):
    archived = json.loads(path.read_text())
    initial, fitted = (np.asarray(archived[key]) for key in ("initial", "fit"))
    panels = []
    for i, domain in generate():
        records = {}
        for label, correlated in (("uniform", False), ("correlated", True)):
            setup = study.environment(domain, study.prior(correlated))
            scores = study.evaluate(domain, setup, initial, fitted)
            records[label] = {"arms": scores, "sum_rule_disagrees_in_worlds": setup[-1]}
        panels.append({"index": i, "domain": domain, "records": records})
    nums = {name: sum(row["records"][p]["arms"][name]["net"] for row, p in product(
                 panels, ("uniform", "correlated"))) / (COUNT * 2)
            for name in panels[0]["records"]["uniform"]["arms"]}
    comparisons = []
    for row in panels:
        for p, record in row["records"].items():
            arms = record["arms"]
            diff = arms["fit"]["net"] - arms["initial"]["net"]
            comparisons.append({"panel": row["index"], "prior": p, "delta": diff,
                                "headroom_for_initial": arms["exact_local"]["net"] - arms["initial"]["net"]})
    tol = 1e-10
    changes = {"fit_wins": sum(r["delta"] > tol for r in comparisons),
               "fit_losses": sum(r["delta"] < -tol for r in comparisons),
               "ties": sum(abs(r["delta"]) <= tol for r in comparisons),
               "initial_at_exact": sum(r["headroom_for_initial"] < tol for r in comparisons)}
    return {"seed": SEED, "count": COUNT, "means": nums, "changes": changes, "comparisons": comparisons,
            "panels": panels, "sha256": {p.name: sha256(p.read_bytes()).hexdigest()
                                       for p in (Path(__file__), Path(study.__file__), path)}}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("fit", type=Path)
    print(json.dumps(evaluate(cli.parse_args().fit), indent=2))
