"""Check receipt-content value with private availability of Russian evidence."""
import argparse
from itertools import product
import json
from pathlib import Path

import numpy as np

import receipt_choice as main

HERE, old, loss = main.HERE, main.old, main.loss
SHARES = (.25, .50, .75)


def plan():
    inputs = (Path(__file__), HERE / "private-protocol.md", HERE / "plan.json", HERE / "results.json",
              Path(main.__file__), Path(old.__file__))
    return {"staffing_probability": list(SHARES), "rates": list(loss.RATES),
            "sha256": {p.name: old.DIGEST(p) for p in inputs}}


def expected(rewards, probabilities, views, policy, desk):
    b, m = np.indices(views.shape)
    sent = policy[views]
    return float(np.sum(probabilities * rewards[b, desk, m, sent]))


def optimal(rewards, probabilities, views):
    rows = []
    for desk in range(rewards.shape[1]):
        payoffs = probabilities[..., None] * rewards[:, desk]
        choices = np.array([int(np.argmax(payoffs[views == view].sum(axis=0)))
                            for view in range(int(views.max()) + 1)])
        rows.append((expected(rewards, probabilities, views, choices, desk), choices.tolist(), desk))
    return max(rows, key=lambda x: x[0])


def run():
    locked = plan()
    assert locked == json.loads((HERE / "private-plan.json").read_text())
    learned = np.array(json.loads((HERE / "results.json").read_text())["training"][-1]["weights"])
    fixed = np.asarray([1., 0., 1.])
    (_, counts, caps, local, edges, score), = [row for row in old.un_cases() if row[0] == "tribunals"]
    choices = old.options(counts, caps)
    true = {ids: [score([choices[i][a] for i, a in enumerate(ids)], mask) for mask in range(8)]
            for ids in product(*(range(len(x)) for x in choices))}
    public = true[(0, 0, 0)][0]
    rows = []
    for share, rate in product(SHARES, loss.RATES):
        distribution = np.array([share, 1. - share])
        scene = main.features(counts, caps, [np.asarray(x) for x in local], edges, (rate,) * 3, true)
        probabilities = distribution[:, None] * scene["mask_probabilities"][None, :]
        assert abs(probabilities.sum() - 1.) <= 1e-10
        full = scene["adaptive"]
        arrived = distribution @ full[1:].reshape(len(distribution), -1)
        arrived = arrived.reshape(full[0].shape)
        observed = scene["observe"]
        channels = {
            "content": (observed, full),
            "arrival": ((observed > 0).astype(int), np.stack((full[0], arrived))),
            "none": (np.zeros_like(observed), ((1 - rate) * full[0] + rate * arrived)[None, :, :]),
        }
        outcomes = {}
        for name, (view, a) in channels.items():
            ceiling, oracle_choices, oracle_last = optimal(scene["returns"], probabilities, view)
            arm = {"oracle": {"expected_release": ceiling + public, "first_desk_by_view": oracle_choices,
                              "third_desk": oracle_last}}
            for predictor, weights in (("learned", learned), ("fixed", fixed)):
                last = int(np.argmax(scene["open"][2] @ weights))
                choices_a = np.argmax(a @ weights, axis=1)
                value = expected(scene["returns"], probabilities, view, choices_a, last)
                assert value <= ceiling + 1e-9
                arm[predictor] = {"expected_release": value + public, "first_desk_by_view": choices_a.tolist(),
                                  "third_desk": last}
            outcomes[name] = arm
        observed_delta = outcomes["content"]["oracle"]["expected_release"] - outcomes["arrival"]["oracle"]["expected_release"]
        predicted = rate ** 2 * (share - max(0., 3 * share - 2))
        assert abs(observed_delta - predicted) < 1e-9
        rows.append({"rate": rate, "staffing_probability": share, "outcomes": outcomes,
                     "oracle_value_of_content_over_arrival": observed_delta})
    return {"rows": rows, "independent_formula_checks": len(rows), "plan_sha256": old.DIGEST(HERE / "private-plan.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run"))
    print(json.dumps({"plan": plan, "run": run}[parser.parse_args().mode](), indent=2))
