"""Allow the script to optimize which requested card a desk sends first."""
import json

import roster_shift as shift

HERE = shift.HERE
relay = shift.relay


def best_scripts(ids, bank, target, anchor, roster):
    a, b = sorted(set(target) - {anchor})
    swap = {i: i if i not in (a, b) else (b if i == a else a) for i in range(len(ids))}
    opposite = {tuple(tuple(sorted(swap[i] for i in holding)) for holding in world): weight
                for world, weight in roster.items()}
    ids_opposite = tuple(ids[swap[i]] for i in range(len(ids)))
    canonical = shift.score(ids, bank, target, anchor, roster, {})
    reversed_order = shift.score(ids_opposite, bank, target, anchor, opposite, {})
    return {name: max((canonical[name], reversed_order[name]), key=lambda x: x["net_gain_over_anchor"])
            for name in canonical}


def run():
    fit = shift.transfer.read(HERE / "specialist-fit-results.json")
    hints = shift.transfer.read(HERE / "specialist-hint-results.json")
    comparison = {}
    for name, ids, bank, _ in shift.datasets():
        cases = {}
        for label, (strength, desk, mode) in shift.CONDITIONS.items():
            if mode == "wrong_hint":
                continue  # Only the public hint differs in this condition.
            scripts = [best_scripts(ids, bank, target, anchor,
                                    shift.distribution(set(target) - {anchor}, strength, desk, mode))
                       for target, anchor in relay.SCENARIOS]
            mean = shift.transfer.mean(scripts)
            expected = fit["transfer"][name][label]["mean"]
            key = "net_gain_over_anchor"
            for route in ("known_prior_fixed", "known_prior_adaptive"):
                assert mean[route][key] >= expected[route][key] - 1e-9
            learned = expected["trained_joint"][key]
            rows = {strategy: stats[key] for strategy, stats in mean.items()}
            row = {"stronger_scripts": rows, "trained_joint": learned,
                   "learned_minus_fixed": learned - rows["known_prior_fixed"],
                   "learned_minus_adaptive": learned - rows["known_prior_adaptive"]}
            if label == "strong_specialist_B":
                invalid = hints["families"][name]["wrong_hint"]
                row["needed_hint_accuracy_vs_stronger_fixed"] = ((rows["known_prior_fixed"] - invalid)
                                                                  / (learned - invalid))
            cases[label] = row
        comparison[name] = cases
    return {"scope": "The comparison script sees the true prior and for each public case chooses the priority "
                     "order in the same two-ID request plus the best fixed or adaptive route. Responder choice "
                     "is then deterministic across both desks. Prior aliases do not change the hidden world.",
            "families": comparison}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
