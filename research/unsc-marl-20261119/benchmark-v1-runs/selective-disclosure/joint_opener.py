"""Fit a factored opening action value from exact team outcomes."""
import json
from pathlib import Path
from statistics import mean
from unittest.mock import patch

import numpy as np
import torch

import selective as s

HERE, shared, base = s.HERE, s.shared, s.base


def basis(d, prior, start):
    grid = d.grid
    outcomes = s.variant(grid, d.states, start)
    table = {}
    for seat in range(len(grid.cards[0])):
        worlds = [w for w in grid.worlds if w[0] == seat]
        weight = sum(prior[w] for w in worlds)
        local = np.array([prior[w]/weight for w in worlds])
        options = []
        for column in range(3):
            pair = np.asarray([outcomes[w, column] for w in worlds])
            observe = pair.copy()
            observe[:, 1] = (1-base.PEER)*pair[:, 0] + base.PEER*pair[:, 1]
            guess = observe.mean(axis=0)
            truth = local @ observe
            grade, _, distinct, cert, remainder, *_ = grid.counsel(0, seat, column, None)
            x = (1., guess[1]-guess[0], grade, distinct, cert, remainder, float(grade == 0))
            options.append(dict(features=x, uniform=guess, actual=truth, weight=weight/3))
        table[seat] = options
    return table


def train(tables):
    items = [r for table in tables for choices in table.values() for r in choices]
    x, y, mass = (np.stack([row[k] for row in items]) for k in ("features", "actual", "weight"))
    base = np.stack([row["uniform"] for row in items])
    w = np.sqrt(mass)
    observations = x*w[:, None]
    labels = (y-base)*w[:, None]
    weights = np.linalg.solve(observations.T@observations + .02*np.eye(x.shape[1]), observations.T@labels)
    return weights, dict(uniform_rmse=float(np.sqrt(np.average(((y-base)**2).mean(1), weights=mass))),
                         fitted_rmse=float(np.sqrt(np.average(((y-base-x@weights)**2).mean(1), weights=mass))))


def choose(d, start, table, weights, fee, arm):
    p = start.copy()
    for seat, options in table.items():
        scores = []
        for option in options:
            value = option["actual"] if arm == "same-recipient-exact" else option["uniform"]
            if arm == "joint-fitted":
                value = value + np.asarray(option["features"])@weights
            scores.extend(value - np.array([0., fee]))
        row = d.states["A", seat]
        p[row] = 0.
        p[row, int(np.argmax(scores))] = 1.
    return p


def run():
    torch.set_num_threads(1)
    registry = s.read(s.original.REGISTRY)
    index = {r["draw"]: r for r in registry["accepted"]}
    frozen = s.read(s.FIT)
    gate = np.array(s.read(HERE / "selective.json")["coef"])
    frozen_weights = torch.tensor(frozen["weights"], dtype=torch.float64)
    old = {r["grid_id"]: r["results"] for r in frozen["reserved"]}
    prose = s.read(s.PROSE)
    mapping = {tuple(r["intended"]): tuple(r["evidence_reader"]) for r in prose["messages"]}
    cost = {tuple(r["intended"]): (r["tokens"]["writer"], r["tokens"]["evidence"]) for r in prose["messages"]}

    def lane(row, balanced):
        with patch.dict(shared.FIXTURES, {"target": s.original.fixture(index[row])}):
            d = shared.Experiment(shared.Grid("target"), balanced)
        for i, role in enumerate(d.roles):
            if role == 2:
                d.mask[i, 1:] = False
        start = d.probabilities(frozen_weights).numpy()
        return d, start, basis(d, d.prior, start)

    weights, fitting = train([lane(i, True)[2] for i in registry["partition"]["fit"]])
    modes = {}
    for mode, balanced in (("balanced", True), ("uniform", False)):
        held = {}
        for i in registry["partition"]["reserved"]:
            d, start, table = lane(i, balanced)
            gate_table = s.summarize(d, start)
            report = {}
            for fee in s.FEES:
                variants = {arm: choose(d, start, table, weights, fee, arm)
                            for arm in ("joint-uniform", "joint-fitted", "same-recipient-exact")}
                variants.update({arm: s.gated(d, start, gate_table, gate, selector, fee)
                                 for arm, selector in (("prior-gate", "fitted"),
                                                       ("uniform-gate", "uniform-forecast"),
                                                       ("exact-gate", "exact-gate"), ("original", "original"))})
                results = {arm: s.measure(d, vals, fee) for arm, vals in variants.items()}
                assert all(r["net"] <= results["same-recipient-exact"]["net"] + 1e-9 for r in results.values())
                row = dict(metrics=results, choices={arm: {
                    str(k): vals[d.states["A", k], :6].tolist() for k in table
                } for arm, vals in variants.items()})
                if fee == base.FEE:
                    binding = {name: s.ledger_metrics(d, vals, mapping, cost) for name, vals in variants.items()}
                    for name, score in binding.items():
                        assert abs(score["net"] - results[name]["net"]) < 1e-9
                    row["language"] = binding
                    if balanced:
                        row["historical_exact_independent"] = old[i]["exact_independent"]["net"]
                        row["historical_exact_peer"] = old[i]["exact_peer"]["net"]
                        assert results["same-recipient-exact"]["net"] <= row["historical_exact_peer"] + 1e-9
                report[fee] = row
            held[i] = report
        summary = {}
        for fee in s.FEES:
            first = next(iter(held.values()))[fee]["metrics"]
            summary[fee] = {arm: {key: mean(row[fee]["metrics"][arm][key] for row in held.values())
                                  for key in ("net", "after_followup", "peer_rate")} for arm in first}
        modes[mode] = dict(held=held, macro=summary)
    from hashlib import sha256
    pins = (Path(__file__), HERE / "joint-opener-protocol.md", HERE / "selective.json")
    return dict(weights=weights.tolist(), training=fitting, evaluation=modes,
                sources={p.name: sha256(p.read_bytes()).hexdigest() for p in pins})


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
