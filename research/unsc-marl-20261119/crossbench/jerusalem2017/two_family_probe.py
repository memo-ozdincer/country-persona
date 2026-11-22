"""Evaluate the stronger scripted control that knows the two intended desk schedules."""
from itertools import permutations
import json
from pathlib import Path

import numpy as np

import relay_population as population
import transfer

HERE = transfer.HERE
HORIZON = 8


def observation_probabilities(schedules, focus, loss):
    request = (1 - loss) * schedules[:, focus]
    return np.column_stack((1 - request, request))


def choose(schedules, calibration):
    loss = calibration.question_loss
    best = (-np.inf, None, None)
    for probe in range(4):
        branch = observation_probabilities(schedules, probe, loss)
        decisions = []
        value = 0.
        for signal in range(2):
            weights = branch[:, signal]
            infer = weights @ schedules / weights.sum()
            receiver = calibration.receiver(infer, calibration.design_prior)
            decisions.append(receiver)
            value += sum(w * calibration.utility(sender, receiver, calibration.design_prior)
                         for w, sender in zip(weights, schedules, strict=True)) / len(schedules)
        value -= (population.PROBE_FEE + calibration.question_fee * schedules[:, probe].mean()) / HORIZON
        if value > best[0] + 1e-12:
            best = (value, probe, decisions)
    return best


def run():
    calibration = transfer.Calibration()
    calibration.points[:, 1] = 70
    points = population.physical_bank()
    population_path = HERE / "relay-population-results.json"
    previous = json.loads(population_path.read_text())["outcomes"]
    intended = np.array([value["mission"] for value in transfer.EXPECTED.values()])
    assert np.array_equal(intended.sum(axis=0), np.ones(4))
    labels = list(transfer.EXPECTED)
    cases = {}
    for permutation in permutations(range(4)):
        order = np.asarray(permutation)
        signature = "".join(map(str, order))
        train = intended[:, order]
        _, probe, decoded = choose(train, calibration)
        for label, schedule in zip(labels, intended, strict=True):
            probability = observation_probabilities(schedule[None, order], probe, calibration.question_loss)[0]
            fee = (population.PROBE_FEE + calibration.question_fee * schedule[order[probe]]) / HORIZON
            total = np.zeros((4, 6))
            for w, table in zip(probability, decoded, strict=True):
                total += w * population.expected_gain(schedule, transfer.translate(table, order), points, calibration,
                                                      calibration.question_loss)
            for prior, p in calibration.priors.items():
                score = 42 + float((total * p).sum()) - fee
                reference = previous[label]["evaluations"][signature]["8"][prior]
                cases.setdefault(label, []).append({"order": signature, "prior": prior, "probed_topic": int(order[probe]),
                                                      "one_probe": score, "four_probe": reference["estimated_channel"],
                                                      "no_probe": reference["exact_no_probe"]})
    out = {}
    for key, details in cases.items():
        margins = np.asarray([row["one_probe"] - row["four_probe"] for row in details])
        out[key] = {"conditions": len(details), "one_probe_wins": int(np.count_nonzero(margins > 1e-9)),
                    "four_probe_wins": int(np.count_nonzero(margins < -1e-9)), "mean_one_probe_minus_four": float(margins.mean()),
                    "minimum_one_probe_minus_four": float(margins.min()), "maximum_one_probe_minus_four": float(margins.max()),
                    "canonical": next(row for row in details if row["order"] == "0123" and
                                      row["prior"] == "correlated_development"), "runs": details}
    return {"scope": "Stronger-information script. It knows that the only possible stable partners are the two intended "
                     "opposite schedules and starts with equal odds. It chooses its single public probe and decoding "
                     "rule with the development prior and pays measured communication costs. The general four-probe "
                     "policy does not restrict the possible schedules to this family.",
            "code_sha256": transfer.routing.digest(Path(__file__)),
            "population_sha256": transfer.routing.digest(population_path), "outcomes": out}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
