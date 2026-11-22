"""Measure ambiguity left by the frozen public feature interface."""
from collections import defaultdict
from hashlib import sha256
from pathlib import Path

import audit as a

HERE = Path(__file__).resolve().parent


def panel(config, rate):
    menu = config["menu"]
    groups, enriched = defaultdict(list), defaultdict(list)
    for world in config["worlds"]:
        req = world["requirements"]
        own = [a.accepted(menu, r) for r in req]
        claims = [(role, option, a.public.signed.claim(f"{i}/{option}", role, option in own[i], option))
                  for i, role in enumerate(a.ROLES) for option in a.OPTIONS]
        for log in a.subsets([claim for _, _, claim in claims]):
            before, points, prior = a.state(menu, log)
            for role, option, claim in claims:
                true = bool(claim.get("accepts"))
                after, final, _ = a.state(menu, [*log, {**claim, "id": "reply"}])
                delta = rate*(final-points)-a.SEND
                x = a.public.features(log, role, option, rate, true)
                datum = {"world": world["id"], "opening": [q["id"] for q in log], "role": role,
                         "queried_option": option, "decision_before": before, "decision_after": after,
                         "verified_sign": true, "send_advantage": delta,
                         "prior_requirements": prior}
                groups[x].append(datum)
                other = a.ROLES[1-a.ROLES.index(role)]
                left_after = sum((option in a.accepted(menu, candidate)) == true for candidate in prior[role])
                enriched[(*x, len(prior[role]), len(prior[other]), left_after)].append(datum)
    return {"original": statistics(groups), "with_candidate_counts": statistics(enriched)}


def statistics(groups):
    bound = oracle = 0.
    sample = []
    conflicting = minimum_errors = 0
    for x, rows in sorted(groups.items()):
        positives = [item for item in rows if item["send_advantage"] > 1e-10]
        nonpositive = [item for item in rows if item["send_advantage"] <= 1e-10]
        value = sum(row["send_advantage"] for row in rows)
        bound += max(0., value)
        oracle += sum(row["send_advantage"] for row in positives)
        if positives and nonpositive:
            conflicting += 1
            minimum_errors += min(len(positives), len(nonpositive))
            sample.append({"features": x, "send": len(positives), "pass": len(nonpositive),
                           "send_witness": positives[0], "pass_witness": nonpositive[0]})
    assert bound <= oracle + 1e-9
    return {"groups": len(groups), "conflicting_groups": conflicting, "minimum_action_errors": minimum_errors,
            "best_constant_action_net": bound, "record_oracle_net": oracle,
            "unavoidable_net_gap": oracle-bound, "witnesses": sample}


def run():
    config = a.E.read(HERE/"case.json")
    paths = (Path(__file__), HERE/"case.json", HERE/"audit.py", HERE/"alias-protocol.md")
    return {"rates": {str(rate): panel(config, rate) for rate in a.RATES},
            "sha256": {path.name: sha256(path.read_bytes()).hexdigest() for path in paths}}


if __name__ == "__main__":
    a.E.emit(run())
