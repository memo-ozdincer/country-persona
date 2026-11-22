"""Use known-valid baseline requests unless surviving partners agree on a gain."""
import argparse
from functools import lru_cache
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

import warrant_language_team_score as interface

study = interface.study
design, world = interface.design, interface.world
HERE = world.HERE
EVIDENCE = HERE / "warrant-request-safety-evidence"
LANGUAGE = study.EVIDENCE / "package-only/results.json"
SEED = interface.adapt.SEED
HISTORIES = interface.adapt.REPLICAS
PREFIXES = (0, 4, 16)
COMPATIBLE_TABLES = world.LOCAL_TABLES


class Planner:

    def __init__(self, task, prior):
        self.task = task
        self.prior = prior
        self.baseline = task.requests(task.weights(np.full((3, 4, 3), 1 / 3.), prior))
        slots, grade_support = interface.receiver.flexible.registry(task)
        self.slots = slots
        self.possible_types = np.zeros((task.num_states, 3, len(COMPATIBLE_TABLES)), dtype=np.uint8)
        for state in range(task.num_states):
            inferred = world.TYPES[grade_support[state]]
            for role, slot in enumerate(slots[state]):
                available = np.isin(np.arange(4), inferred[:, role])
                compatible = COMPATIBLE_TABLES == slot
                if slot < 0:
                    self.possible_types[state, role] = 15
                else:
                    self.possible_types[state, role] = (compatible & available) @ np.array([1, 2, 4, 8], dtype=np.uint8)
        # Same current evidence and hidden world imply identical net returns,
        # regardless of which opening actions were taken and lost.
        self.pay = np.zeros((task.num_states, 64, 10))
        for w in range(64):
            self.pay[task.state[w].ravel(), w] = task.pay[w].reshape(-1, 10)
        self.bits = (1 << world.TYPES.T)

    def table_support(self, histories):
        if not len(histories):
            return tuple(tuple(range(len(COMPATIBLE_TABLES))) for _ in range(3))
        return tuple(tuple(np.flatnonzero((self.possible_types[histories, role] != 0).all(0)))
                     for role in range(3))

    @lru_cache(maxsize=30000)
    def decision(self, state, support):
        baseline = self.baseline[state]
        groups = []
        for role in range(3):
            if not support[role]:
                return int(baseline), 0.
            choices = np.unique(self.possible_types[state, role, list(support[role])])
            present = [(self.bits[role] & index) != 0 for index in choices if index]
            if not present:
                return int(baseline), 0.
            groups.append(present)
        p = np.asarray([self.prior * a * b * c for a, b, c in product(*groups)])
        p = p[p.sum(-1) > 0.]
        if not len(p):
            return int(baseline), 0.
        p /= p.sum(-1, keepdims=True)
        action_values = p @ (self.pay[state] - self.pay[state, :, baseline, None])
        minimum = np.where(self.task.legal[state], action_values.min(0), -np.inf)
        best = int(minimum.argmax())
        return (best, float(minimum[best])) if minimum[best] > 1e-12 else (int(baseline), 0.)


def evaluate(planner, calibration, actual, occurrences, draws, stable):
    cdf = np.cumsum(calibration)
    history = np.searchsorted(cdf, draws, side="right")
    assert np.all(calibration[history] > 0.)
    reachable = np.flatnonzero(occurrences > 0.)
    table = planner.baseline
    own = interface.metric(planner.task, actual, occurrences, table)
    best = interface.metric(planner.task, actual, occurrences, design.choose(planner.task, actual))
    results = {"grade_only": own, "known_partner": best}
    for n in PREFIXES:
        queries = []
        lower = []
        for prior_episodes in history[:, :n]:
            support = planner.table_support(prior_episodes)
            q = table.copy()
            certified_gain = 0.
            for state in reachable:
                pick, minimum = planner.decision(int(state), support)
                q[state] = pick
                certified_gain += occurrences[state] * minimum
            queries.append(q)
            lower.append(certified_gain)
        choices = np.asarray(queries)
        result = interface.metric(planner.task, actual, occurrences, choices)
        result["mean_lower_gain_bound"] = float(np.mean(lower))
        cert_state = np.arange(planner.task.num_states)
        gain = actual[cert_state, choices].sum(1) - own["mean_net"]
        result["min_history_gain"] = float(gain.min())
        result["negative_histories"] = int(np.sum(gain < -1e-12))
        result["changed_request_probability"] = float(((choices != table) * occurrences).sum(1).mean())
        if stable:
            assert np.all(gain >= np.asarray(lower) - 1e-12)
        assert result["mean_net"] <= best["mean_net"] + 1e-12
        results[str(n)] = result
    return results


def run():
    gen = np.random.default_rng(SEED)
    output = {"language": [], "synthetic": []}
    previous = json.loads(LANGUAGE.read_text())["replay"]["domains"]
    fit = json.loads(design.PREVIOUS.read_text())
    weights = np.asarray(fit["fitted_weights"])
    for test in previous:
        task = world.Workshop(np.asarray(test["cards"]))
        plans = np.asarray(test["admitted_slots"])
        assert (plans >= 0).all()
        for label in ("uniform", "correlated"):
            p = world.prior(label == "correlated")
            u, occ = interface.actual_values(task, p, plans)
            planner = Planner(task, p)
            result = evaluate(planner, occ, u, occ, gen.random((HISTORIES, 16)), True)
            output["language"].append({"domain": test["domain"], "prior": label, "scores": result})
            planner.decision.cache_clear()
    for test in fit["results"]:
        task = world.Workshop(np.asarray(test["cards"]))
        for label, old in test["priors"].items():
            p = world.prior(label == "correlated")
            planner = Planner(task, p)
            teams = design.partners(task, p, weights, old["arms"]["coordinate"]["opening_table"])
            mixed, coordinate = [interface.actual_values(task, p, teams[key]) for key in ("mixed", "coordinate")]
            draws = gen.random((HISTORIES, 16))
            scores = {key: evaluate(planner, occ, u, occ, draws, True)
                      for key, (u, occ) in zip(("mixed", "coordinate"), (mixed, coordinate), strict=True)}
            scores["switch_to_coordinate"] = evaluate(planner, mixed[1], *coordinate, draws, False)
            output["synthetic"].append({"domain": test["i"], "prior": label, "scores": scores})
            planner.decision.cache_clear()
    paths = (Path(__file__), EVIDENCE / "protocol.md", LANGUAGE, design.PREVIOUS,
             Path(world.__file__), Path(interface.__file__))
    return {"seed": SEED, "histories": HISTORIES, "prefixes": PREFIXES, **output,
            "sha256": {str(p.relative_to(HERE)): sha256(p.read_bytes()).hexdigest() for p in paths}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(run(), indent=2))
