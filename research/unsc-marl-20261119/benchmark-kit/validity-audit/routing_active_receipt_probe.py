"""Design a paid receipt probe for the two indistinguishable-prior witnesses."""
import argparse
import json
from math import factorial
from pathlib import Path

import numpy as np

import routing_receipt_identifiability as ident

base, route, robust, pilot = ident.base, ident.route, ident.robust, ident.pilot
PROBES, FUTURE = 8, 64


def compositions(n, parts):
    if parts == 1:
        yield (n,)
        return
    for first in range(n + 1):
        for tail in compositions(n - first, parts - 1):
            yield (first, *tail)


def observation_law(counts, prob, multinomial):
    zero = prob == 0
    log = np.log(np.where(zero, 1., prob))
    result = multinomial * np.exp(counts @ log)
    result[(counts @ zero) > 0] = 0
    assert abs(result.sum() - 1) < 1e-9
    return result


def solve_case(policies, planned, actual, distributions):
    # One episode can deliver at most two fields. The all-three mask has zero probability.
    rows = np.array(list(compositions(PROBES, 7)))
    fact = np.array([factorial(i) for i in range(PROBES + 1)])
    multinomial = factorial(PROBES) / fact[rows].prod(axis=1)
    data = []
    for label, policy in policies.items():
        k = ident.receipt_kernel(policy)
        for role in ("forward", "swapped"):
            swapped = role == "swapped"
            probs = [np.einsum("rls,ls->r", k, p.T if swapped else p) for p in distributions]
            assert all(abs(x[7]) < 1e-12 for x in probs)
            planned_value = pilot.cell_returns(policy, planned)
            actual_value = pilot.cell_returns(policy, actual)
            def expectation(values):
                return np.array([np.sum(values * (p.T if swapped else p)) for p in distributions])
            data.append({"key": f"{role}:{label}", "laws": [observation_law(rows, x[:7], multinomial) for x in probs],
                         "planned": expectation(planned_value), "actual": expectation(actual_value)})
    public = np.stack([x["planned"] for x in data])
    realized = np.stack([x["actual"] for x in data])
    fallback = public.mean(axis=1).argmax()
    no_probe = data[fallback]
    choices = []
    for candidate in data:
        probs = np.stack(candidate["laws"], axis=1) * .5
        post = probs @ public.T
        decisions = post.argmax(axis=1)
        value = post[np.arange(len(rows)), decisions].sum()
        selected = realized[decisions]
        actual_future = float((probs * selected).sum())
        acquisition = PROBES * float(candidate["planned"].mean())
        realized_acquisition = PROBES * float(candidate["actual"].mean())
        choices.append({"probe": candidate["key"],
                        "classification_accuracy": float(probs.max(axis=1).sum()),
                        "planned_total": float(acquisition + FUTURE * value),
                        "observed_total": float(realized_acquisition + FUTURE * actual_future),
                        "future_net": actual_future,
                        "probe_reward_deficit": float(PROBES * no_probe["actual"].mean() - realized_acquisition)})
    no_probe_plan = (PROBES + FUTURE) * float(no_probe["planned"].mean())
    no_probe_actual = (PROBES + FUTURE) * float(no_probe["actual"].mean())
    best = max(choices, key=lambda x: x["planned_total"])
    chosen = best if best["planned_total"] > no_probe_plan + 1e-9 else None
    return {"receipt_histograms": len(rows), "probe_candidate_count": len(data), "no_probe_arm": no_probe["key"],
            "no_probe_planned_total": no_probe_plan, "no_probe_observed_total": no_probe_actual,
            "best_probe": best, "probe_adopted": chosen is not None,
            "observed_total_gain": chosen["observed_total"] - no_probe_actual if chosen else 0.}


def run(anchor_file, witness_file):
    anchors = json.loads(anchor_file.read_text())
    witness = json.loads(witness_file.read_text())
    assert witness["input_sha256"][anchor_file.name] == base.space.runner.digest(anchor_file)
    cases = {}
    for name, checksum, wanted, observed in base.held_out():
        item = witness["historical"][name]
        assert checksum == item["source_sha256"]
        pool = {key: base.space.as_policy(p) for key, p in anchors["historical"][name]["pool"].items()}
        distributions = [np.asarray(item[label]) for label in ("prior_a", "prior_b")]
        cases[name] = solve_case(pool, route.receipt_matrix(wanted, route.TRAIN_LOSS),
                                 route.receipt_matrix(observed, route.TRAIN_LOSS), distributions)
    return {"scope": "Known, equally likely synthetic hypotheses from the passive-receipt aliasing test. "
                     "Select one probe policy for eight in-task pilot episodes and a future policy from "
                     "the resulting receipt histogram. Fees and opportunity cost for the eight episodes are "
                     "included. There are no disclosures of joint inventories and no new text generation.",
            "pilot_episodes": PROBES, "future_episodes": FUTURE, "cases": cases,
            "input_sha256": {p.name: base.space.runner.digest(p) for p in (anchor_file, witness_file)},
            "scorer_sha256": base.space.runner.digest(Path(__file__))}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--anchor", type=Path, default=robust.OUT / "report.json")
    cli.add_argument("--witness", type=Path, default=robust.OUT / "receipt-identifiability.json")
    args = cli.parse_args()
    print(json.dumps(run(args.anchor, args.witness), indent=2))
