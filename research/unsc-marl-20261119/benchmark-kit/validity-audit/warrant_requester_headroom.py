"""Measure requester headroom across distinct opening partners."""
import argparse
import json
from pathlib import Path

import numpy as np

import warrant_three as world

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "warrant-requester-evidence"
PREVIOUS = world.EVIDENCE / "results.json"
TRAIN_PARTNERS = ("fitted", "top_grade", "veto_first")
HOLD_PARTNERS = (*TRAIN_PARTNERS, "coordinate", "mixed")


def partners(task, p, learned, transferred=None):
    grade = task.cards
    features = task.features(p)
    fitted = (features * learned[:, None, None]).sum(-1).argmax(-1)
    top = grade.argmax(-1)
    veto = np.where((grade == 0).any(-1), (grade == 0).argmax(-1), top)
    opening = {"fitted": fitted, "top_grade": top, "veto_first": veto, "mixed": np.stack((veto[0], top[1], fitted[2]))}
    if transferred is not None:
        opening["coordinate"] = np.asarray(transferred)
    return opening


def returns(task, mass):
    numerator = np.zeros((task.num_states, 10))
    events = mass[:, :, None] * world.P_LINKS
    np.add.at(numerator, task.state.ravel(), (events[..., None] * task.pay).reshape(-1, 10))
    prevalence = np.bincount(task.state.ravel(), weights=events.ravel(), minlength=task.num_states)
    return numerator, prevalence


def choose(task, utility):
    return np.where(task.legal, utility, -np.inf).argmax(-1)


def contrast(task, p, learned, coordinate):
    tables = partners(task, p, learned, coordinate)
    masses = {name: task.weights(np.eye(3)[table], p) for name, table in tables.items()}
    uniform = task.weights(np.full((3, 4, 3), 1 / 3.), p)
    mixture = np.mean([masses[key] for key in TRAIN_PARTNERS], axis=0)
    assumed = {"grade_only": uniform, "fit_assumed": masses["fitted"], "training_mixture": mixture}
    biased = {name: task.requests(source) for name, source in assumed.items()}
    measurements = {}
    for partner, actual in masses.items():
        candidates = {**biased, "partner_known": task.requests(actual),
                      "opening_only": np.zeros(task.num_states, dtype=int)}
        score = {key: task.metrics(actual, q) for key, q in candidates.items()}
        assert all(score["partner_known"]["net"] + 1e-12 >= v["net"] for v in score.values())
        measurements[partner] = score
    return measurements


def run(fit):
    old = json.loads(fit.read_text())
    learned = np.asarray(old["fitted_weights"])
    panels = []
    for row in old["results"]:
        task = world.Workshop(np.asarray(row["cards"]))
        priors = {}
        for label, archived in row["priors"].items():
            p = world.prior(label == "correlated")
            priors[label] = contrast(task, p, learned, archived["arms"]["coordinate"]["opening_table"])
        panels.append({"domain": row["i"], "priors": priors})
    return {"rows": panels, "training_partner_mixture": TRAIN_PARTNERS}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("fit", type=Path, default=PREVIOUS, nargs="?")
    print(json.dumps(run(cli.parse_args().fit), indent=2))
