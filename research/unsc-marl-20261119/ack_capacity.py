"""Bound certificate gains for the exact local views used by ack deferral."""
from collections import Counter, defaultdict
import json

import ack_deferral_fit as train


def evaluate():
    views = defaultdict(Counter)
    panels = {}
    for family, regimes in train.audit.samples():
        if family == "fresh_synthetic":
            continue
        panels[family] = train.cohort(regimes)
        for name, rows in panels[family].items():
            for group, obs, immediate, deferred in rows:
                if obs is None:
                    continue
                delta = int(deferred[0])-int(immediate[0])
                views[obs][family,name,group,str(delta)] += 1

    safe, by_regime = {}, {}
    for local, outcomes in views.items():
        safe[local] = not any(k[-1] == "-1" for k in outcomes) and any(k[-1] == "1" for k in outcomes)
        for name in {k[1] for k in outcomes}:
            within = {k for k in outcomes if k[1] == name}
            by_regime[local,name] = not any(k[-1] == "-1" for k in within) and any(k[-1] == "1" for k in within)
    flatten = train.fit.router.sp.flatten
    groups = {
        "".join(map(lambda bit: str(int(bit)), view)): {
            "preserves_all_certificates": safe[view], "counts": flatten(values),
            "has_rescue": any(k[-1] == "1" for k in values), "has_regression": any(k[-1] == "-1" for k in values),
        } for view, values in sorted(views.items())
    }
    results = {}
    for family, regimes in panels.items():
        results[family] = {}
        for name, rows in regimes.items():
            results[family][name] = {
                "individual_episode_oracle": sum(max(int(before[0]),int(after[0])) for _,_,before,after in rows),
                "shared_local_protected": train.gate.score(rows, lambda obs: not safe[obs]),
                "known_regime_protected": train.gate.score(rows, lambda obs: not by_regime[obs,name]),
            }
    return {"scope": "In-sample upper bounds preserving each baseline certificate, under one reversible deferral and the same public status. The shared table sees only the exact actor features; the known-regime table is an extra-information control.",
            "observations": groups, "results": results}


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
