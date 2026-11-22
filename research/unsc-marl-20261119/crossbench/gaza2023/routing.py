"""Exact local-information and scripted ceilings for the Gaza archive simulation."""
import argparse
from hashlib import sha256
from itertools import combinations, permutations, product
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
PAIR = np.asarray(list(combinations(range(4), 2)))
REQUESTS = np.asarray(list(product((0, 1), repeat=4)))
PRIORITIES = np.asarray([[next(field for field in ranking if field in held) for held in PAIR]
                         for ranking in permutations(range(4))])
OPTIONS = np.eye(4, dtype=int)[PAIR].sum(axis=1).astype(bool)
ENCODING = {
    "uniform": [[1] * 6 for _ in range(4)],
    "correlated_development": [
        [4, 26, 12, 3, 20, 9], [19, 7, 12, 23, 2, 5], [28, 24, 3, 23, 3, 19], [6, 16, 3, 12, 16, 19]
    ],
    "correlated_diagnostic_2": [
        [10, 1, 15, 6, 21, 1], [2, 7, 16, 27, 12, 18], [26, 22, 24, 1, 9, 14], [2, 22, 27, 18, 23, 13]
    ],
    "correlated_diagnostic_3": [
        [1, 25, 18, 27, 2, 3], [18, 21, 16, 17, 1, 9], [12, 10, 5, 19, 6, 25], [23, 9, 2, 2, 16, 14]
    ],
}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def load():
    data = json.loads((HERE / "task.json").read_text())
    accession = json.loads((HERE / "accession.json").read_text())
    assert accession["task_sha256"] == digest(HERE / "task.json")
    assert len(data["public_criteria"]) == 5 and len(data["focuses"]) == 4
    assert all(len(focus["backup_criteria"]) == 4 for focus in data["focuses"])
    return data


def priors():
    for name, counts in ENCODING.items():
        table = np.asarray(counts, float)
        yield name, table / table.sum()
    # These independent diagnostic draws were kept whole, without choosing on outcome.
    for index, raw in enumerate(np.random.default_rng(170524).integers(1, 30, (6, 4, 6))):
        yield f"unselected_{index + 1}", raw / raw.sum()


def config():
    sim = load()["simulation"]
    return tuple(sim[key] for key in ("question_loss", "reply_loss", "question_cost", "reply_cost"))


def masses(prior, question_loss):
    # Axes: sender policy, observed request, responder inventory, correct field.
    channel = (1 - question_loss) * np.eye(2)[REQUESTS] + question_loss * np.asarray([1, 0])
    return np.einsum("eiq,ir->eqri", channel, prior)


def measure(prior, sender, receiver):
    q_loss, r_loss, q_cost, r_cost = config()
    gross = 42.0
    requests = 0.0
    delivered = 0.0
    for focus, pair in product(range(4), range(len(PAIR))):
        weight = prior[focus, pair]
        request = int(sender[focus])
        requests += weight * request
        for keep, fraction in ((0, q_loss), (1, 1 - q_loss)):
            called = receiver[pair, request * keep]
            assert called in PAIR[pair]
            delivered += weight * fraction * (1 - r_loss) * (called == focus)
    gross += 28 * delivered
    return {"credit": gross, "net": gross - q_cost * requests - r_cost, "request_probability": requests,
            "probability_of_correct_backup_delivery": delivered}


def optimize(prior):
    q_loss, r_loss, q_cost, r_cost = config()
    mass = masses(prior, q_loss)
    costs = q_cost * (REQUESTS @ prior.sum(axis=1)) + r_cost
    flexible = np.where(OPTIONS, mass, -1).argmax(axis=-1)
    rank_value = np.einsum("eqri,pri->eqp", mass, np.eye(4)[PRIORITIES])
    priority = PRIORITIES[rank_value.argmax(axis=-1)]
    switched = PAIR.sum(axis=1) - PRIORITIES
    switch_value = rank_value[:, 0] + np.einsum("eri,pri->ep", mass[:, 1], np.eye(4)[switched])
    positions = switch_value.argmax(axis=-1)
    alternate = np.stack((PRIORITIES[positions], switched[positions]), axis=1)
    def best(tables, fixed=None):
        selected = (mass * np.eye(4)[tables]).sum(axis=(1, 2, 3))
        values = 42 + (1 - r_loss) * 28 * selected - costs
        idx = int(values.argmax()) if fixed is None else fixed
        schedule, replies = REQUESTS[idx], tables[idx].T
        result = measure(prior, schedule, replies)
        assert np.isclose(result["net"], values[idx])
        return {"sender": schedule.tolist(), "receiver": replies.tolist(), **result}
    outcomes = {"silent_pair": best(flexible, fixed=0), "first_or_other": best(alternate),
                "independent_priority_by_request": best(priority), "exact_interactive": best(flexible)}
    upper = 42 + (1 - r_loss) * 28 * (prior.T * OPTIONS).sum() - r_cost
    values = [entry["net"] for entry in outcomes.values()]
    assert values[2] >= values[1] - 1e-9 and values[3] >= max(values[:3]) - 1e-9
    assert upper >= values[3] - 1e-9

    # Independent exhaustive flexible-table check on the 16 x 4096 joint policies.
    # Each inventory/message pair has exactly two possible notes.
    choices = np.asarray(list(product((0, 1), repeat=12))).reshape(-1, 2, 6)
    tables = PAIR[np.arange(len(PAIR)), choices]
    value = np.einsum("eqri,tqri->et", mass, np.eye(4)[tables])
    brute = (42 + (1 - r_loss) * 28 * value - costs[:, None]).max()
    assert np.isclose(brute, values[3])

    return {"policies": outcomes, "full_information_upper": float(upper),
            "interactive_gain_over_silent_pair": values[3] - values[0],
            "interactive_gain_over_best_priorities": values[3] - values[2],
            "joint_policies_checked": int(value.size)}


def report():
    task = load()
    return {"task": task["id"], "task_sha256": digest(HERE / "task.json"),
            "accession_sha256": digest(HERE / "accession.json"),
            "candidate_counts": {"sender": len(REQUESTS), "rankings_per_signal": len(PRIORITIES),
                                 "independent_rank_pairs": len(PRIORITIES)**2},
            "focus_order": [focus["id"] for focus in task["focuses"]],
            "responder_inventory_order": PAIR.tolist(),
            "scope": "Expected available-evidence credit with declared loss and fees. "
                     "The four historical focuses share one event family. Their availability distributions are simulated. "
                     "All algorithms may be given the evaluation prior. A fully flexible Bayesian script reaches the exact optimum.",
            "results": {name: {"prior": prior.tolist(), **optimize(prior)} for name, prior in priors()}}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.parse_args()
    print(json.dumps(report(), indent=2))
