"""Rank learned decentralized tables on public rewards, before private inventories."""
import json

import numpy as np

import routing_paired_reward_fit as revised

base, route, contrasts = revised.base, revised.route, revised.contrasts
OUT = revised.OUT / "portfolio.json"
UNIFORM = "uniform"


def library():
    old, mean = contrasts.read_frozen()
    archive = json.loads((revised.OUT / "report.json").read_text())
    trained = np.asarray(archive["profile_bank"])
    weights = revised.OUT / "weights.pt"
    assert base.space.runner.digest(weights) == archive["weights_sha256"]
    new = contrasts.load(weights)
    high = trained[np.arange(len(trained)) % 4 < 2].mean(axis=0)
    cores = {"original_mean": base.choose(old, mean), "paired_high_mean": base.choose(new, high)}
    silent = tuple(np.zeros(size, dtype=int) for size in ((8,), (8,), (8, 4)))
    policy = {"skip_all": silent}
    for label, core in cores.items():
        for order in base.ORDERS:
            target = base.remap_policy(core, order)
            if not any(all(np.array_equal(a, b) for a, b in zip(target, prev, strict=True))
                       for prev in policy.values()):
                policy[f"{label}-{''.join(str(i) for i in order)}"] = target
    assert len(policy) > 2
    return archive, policy


def choose(library, payoff, prior, admit_independence):
    controls = dict(library)
    if admit_independence:
        matrix = route.receipt_matrix(payoff, route.TRAIN_LOSS)
        controls["optimized_independence"] = route.best_silent(prior, matrix)
    scores = {key: contrasts.measure(p, payoff, prior)["net"] for key, p in controls.items()}
    key = max(scores, key=scores.__getitem__)
    return key, scores[key], controls[key]


def compare(library, intended, actual, exact):
    chosen = {}
    rows = {}
    for label, use_silent in (("library", False), ("with_independence", True)):
        selected = {}
        for p, prior in route.TEST_PRIORS.items():
            row = choose(library, intended, prior, use_silent)
            selected[p] = row
        chosen[label] = {p: {"arm": v[0], "planned_net": v[1]} for p, v in selected.items()}
        rows[label] = {}
        for p, prior in route.TEST_PRIORS.items():
            scores = {"fixed_uniform_choice": contrasts.measure(selected[UNIFORM][2], actual, prior),
                      "prior_supplied": contrasts.measure(selected[p][2], actual, prior)}
            for stat in scores.values():
                assert stat["net"] <= exact[p]["ceiling"] + 1e-9
            rows[label][p] = {**scores, **exact[p]}
    return {"chosen": chosen, "results": rows}


def run():
    archive, pool = library()
    outcomes = {}
    for name, reward in contrasts.rewards().items():
        exact = {p: {m: row[m] for m in ("independent", "ceiling")} for p, row in
                 archive["contrast_outcomes"][name]["priors"].items()}
        outcomes[name] = compare(pool, reward, reward, exact)
    transfer = {}
    for name, checksum, intended, actual in base.held_out():
        held_out = archive["historical_replay"][name]
        assert checksum == held_out["source_sha256"]
        controls = {p: {"independent": row["independent"]["net"], "ceiling": row["exact_optional"]["net"]}
                    for p, row in held_out["priors"].items()}
        transfer[name] = compare(pool, intended, actual, controls)
    result = {"scope": "Frozen synthetic checkpoints. Rank candidate tables by their expected net on the public "
                       "rubric. Main choice uses the nominal uniform prior. The supplied-prior control is reported "
                       "separately. Historical realized records enter scoring only. No new gradient updates.",
              "candidate_count": len(pool), "source_report_sha256": base.space.runner.digest(revised.OUT / "report.json"),
              "contrast": outcomes, "historical_replay": transfer}
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"candidate_count": len(pool), "scope": result["scope"]}, indent=2))


if __name__ == "__main__":
    run()
