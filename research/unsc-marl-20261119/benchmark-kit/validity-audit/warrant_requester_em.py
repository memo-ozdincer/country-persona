"""Fit each role's opening likelihood from publicly observed receipt histories."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

import warrant_requester_adapt as prior

design = prior.design
world = prior.world
MODELS = ("uniform_prior_em", "style_prior_em")
TARGETS = ("mixed", "coordinate")
STEPS = 16
PSEUDOCOUNTS = 2.
ITERATIONS = 20


def registry(task):
    # Recover each receipt state using the immutable reports it contains.
    receipt = {}
    for w, s, l in product(range(64), range(27), range(8)):
        state = int(task.state[w, s, l])
        facts = tuple((i, slot, task.world[w, i, slot]) for i, slot in enumerate(world.SLOTS[s])
                      if world.LINKS[l, i])
        if state in receipt:
            assert receipt[state] == facts
        else:
            receipt[state] = facts
    slots = np.full((task.num_states, 3), -1, dtype=int)
    allowed = np.ones((task.num_states, 64), dtype=bool)
    for state, facts in receipt.items():
        for role, slot, grade in facts:
            slots[state, role] = slot
            allowed[state] &= task.world[:, role, slot] == grade
    return slots, allowed


def fit_histories(ledger, support, observed, p, start):
    frames = ledger[observed]
    known = support[observed]
    present = frames >= 0
    frames = np.maximum(frames, 0)
    r = np.arange(len(frames))[:, None, None, None]
    roles = np.arange(3)[None, None, None, :]
    types = world.TYPES[None, None, :, :]
    slots = frames[:, :, None, :]
    disclosure = np.eye(3)[frames] * present[..., None]
    role_types = np.eye(4)[world.TYPES]
    local = np.broadcast_to(start, (len(frames), 3, 4, 3)).copy()
    for _ in range(ITERATIONS):
        likelihood = np.where(present[:, :, None, :], local[r, roles, types, slots], 1.).prod(-1)
        posterior = likelihood * known * p
        normalizer = posterior.sum(-1, keepdims=True)
        assert (normalizer > 0.).all()
        posterior /= normalizer
        in_types = np.einsum("rhw,wsi->rhsi", posterior, role_types)
        counts = np.einsum("rhsj,rhsi->rsij", disclosure, in_types) + PSEUDOCOUNTS * start
        local = counts / counts.sum(-1, keepdims=True)
    assert np.allclose(local.sum(-1), 1.) and (local > 0.).all()
    return local


def run(path):
    old = json.loads(path.read_text())
    weights = np.asarray(old["fitted_weights"])
    rng = np.random.default_rng(prior.SEED)
    reports = []
    for row in old["results"]:
        task = world.Workshop(np.asarray(row["cards"]))
        ledger, support = registry(task)
        for title, p_row in row["priors"].items():
            p = world.prior(title == "correlated")
            draws = rng.random((prior.REPLICAS, STEPS))
            known_styles = design.partners(task, p, weights, p_row["arms"]["coordinate"]["opening_table"])
            starts = {"uniform_prior_em": np.full((3, 4, 3), 1 / 3.),
                      "style_prior_em": (1 - prior.CONTAMINATION) *
                      np.stack([np.eye(3)[known_styles[k]] for k in design.TRAIN_PARTNERS]).mean(0) +
                      prior.CONTAMINATION / 3.}
            result = {}
            for team in TARGETS:
                actual = task.weights(np.eye(3)[known_styles[team]], p)
                utility, prevalence = design.returns(task, actual)
                history = prior.observations(task, actual, draws)
                result[team] = {}
                for key in MODELS:
                    learned = fit_histories(ledger, support, history, p, starts[key])
                    practice = [task.requests(task.weights(opening, p)) for opening in learned]
                    result[team][key] = prior.exact_evaluate(task, actual, utility, prevalence, np.asarray(practice))
            reports.append({"domain": row["i"], "prior": title, "teams": result})
    files = (Path(__file__), Path(prior.__file__), path)
    return {"rows": reports, "iterations": ITERATIONS, "ordinary_prior_episodes": STEPS,
            "pseudocounts_per_role_card_type": PSEUDOCOUNTS,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("fit", type=Path, nargs="?", default=design.PREVIOUS)
    print(json.dumps(run(cli.parse_args().fit), indent=2))
