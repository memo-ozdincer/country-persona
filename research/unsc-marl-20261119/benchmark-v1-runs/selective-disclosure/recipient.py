"""Learn recipient action values with a frozen, openly specified opener."""
import json
from itertools import permutations, product
from pathlib import Path
from statistics import mean
from unittest.mock import patch

import numpy as np
import torch

import family_transfer as exact
import joint_opener as opener
import selective as s

HERE, shared, base = s.HERE, s.shared, s.base
ARMS = ("frozen", "receipt-only", "policy-aware", "fitted", "exact-recipient")


def cert_reward(grid, a, b):
    result = 0.
    for da, db in product((False, True), repeat=2):
        pa = base.DELIVER if da else 1-base.DELIVER
        pb = base.DELIVER if db else 1-base.DELIVER
        view = (a if da else None, b if db else None)
        result += pa*pb*bool(grid.information(view)[1])
    return result


def aggregate(d, opening):
    grid = d.grid
    moments = {}
    for world in grid.worlds:
        a_index = d.states[("A", world[0])]
        for k, (col, pay) in enumerate(base.ACTIONS):
            a = grid.claim(world, 0, col)
            b_scores = np.array([cert_reward(grid, a, grid.claim(world, 1, b)) for b in range(3)])
            for receipt, delivery in base.observations(a, pay):
                key = ("B", world[1], receipt)
                if key not in moments:
                    moments[key] = np.zeros((3, 4))
                actual_opener = opening[a_index, k]
                # Three forecast populations with the same available recipient actions.
                mass = delivery*np.array([1/6, actual_opener, actual_opener*d.prior[world]])
                moments[key][:, :3] += mass[:, None]*b_scores
                moments[key][:, 3] += mass

    expected = {}
    for key, entries in moments.items():
        assert entries[0, 3] > 0.
        if entries[1, 3] == 0:
            assert entries[2, 3] == 0.
            continue
        assert entries[2, 3] > 0.
        forecasts = entries[:, :3]/entries[:, 3, None]
        features = [grid.counsel(1, key[1], col, key[2]) for col in range(3)]
        x = np.column_stack((np.ones(3), forecasts[1], forecasts[0],
                             np.asarray(features)[:, (0, 2, 3, 4, 7, 8)]))
        expected[key] = dict(x=x, raw=forecasts[0], informed=forecasts[1],
                             true=forecasts[2], weight=float(entries[2, 3]),
                             receipt_rate=float(entries[1, 3]))
    assert np.isclose(sum(row["weight"] for row in expected.values()), 1.)
    return expected


def fit(training):
    rows = [r for table in training for r in table.values()]
    x, p, y = (np.concatenate([row[k] for row in rows]) for k in ("x", "informed", "true"))
    w = np.repeat([r["weight"]/3 for r in rows], 3)
    a = x*np.sqrt(w[:, None])
    target = (y-p)*np.sqrt(w)
    coef = np.linalg.solve(a.T@a + .02*np.eye(x.shape[1]), a.T@target)
    return coef, dict(observations=len(w), input_dim=x.shape[-1],
                      forecast_rmse=float(np.sqrt(np.average((y-p)**2, weights=w))),
                      fitted_rmse=float(np.sqrt(np.average((y-p-x@coef)**2, weights=w))))


def policies(d, opening, table, weights):
    result = {}
    for arm in ARMS:
        selected = opening.copy()
        expected = 0.
        chosen = []
        for state, row in table.items():
            index = d.states[state]
            if arm != "frozen":
                ranks = {"receipt-only": row["raw"], "policy-aware": row["informed"],
                         "fitted": row["informed"]+row["x"]@weights, "exact-recipient": row["true"]}
                action = int(ranks[arm].argmax())
                selected[index] = 0.
                selected[index, action] = 1.
                chosen.append(dict(local_card=state[1], peer=state[2], action=action))
            expected += row["weight"]*float(selected[index, :3]@row["true"])
        actual = s.measure(d, selected, base.FEE)
        assert abs(expected-actual["after_followup"]) < 1e-9
        result[arm] = (selected, actual, chosen)
    target = result["exact-recipient"][1]["net"]
    assert all(value["net"] <= target+1e-9 for _, value, _ in result.values())
    spend = [r[1]["peer_rate"] for r in result.values()]
    assert max(spend)-min(spend) < 1e-9
    return result


def run():
    torch.set_num_threads(1)
    registry = s.read(s.original.REGISTRY)
    index = {row["draw"]: row for row in registry["accepted"]}
    frozen = s.read(s.FIT)
    previous = s.read(HERE / "joint-opener.json")
    w = torch.as_tensor(frozen["weights"], dtype=torch.float64)
    first_weights = np.asarray(previous["weights"])
    prose = s.read(s.PROSE)
    mapping = {tuple(r["intended"]): tuple(r["evidence_reader"]) for r in prose["messages"]}
    costs = {tuple(r["intended"]): (r["tokens"]["writer"], r["tokens"]["evidence"]) for r in prose["messages"]}

    def lane(grid, balanced):
        d = shared.Experiment(grid, balanced)
        for ix, role in enumerate(d.roles):
            if role == 2:
                d.mask[ix, 1:] = False
        start = d.probabilities(w).numpy()
        base_est = opener.basis(d, d.prior, start)
        first = opener.choose(d, start, base_est, first_weights, base.FEE, "joint-fitted")
        return d, first, aggregate(d, first)

    def setup(draw):
        with patch.dict(shared.FIXTURES, {"target": s.original.fixture(index[draw])}):
            return shared.Grid("target")

    fit_ids, reserved = (registry["partition"][k] for k in ("fit", "reserved"))
    assert not set(fit_ids) & set(reserved)
    training = [lane(setup(draw), True)[2] for draw in fit_ids]
    coef, training_stats = fit(training)

    def replay(grid, balanced, use_language):
        d, first, table = lane(grid, balanced)
        result = policies(d, first, table, coef)
        scores = {arm: row[1] for arm, row in result.items()}
        scores.update({"exact-independent": exact.solve(d, False), "exact-team": exact.solve(d, True)})
        assert all(v["net"] <= scores["exact-team"]["net"]+1e-9 for v in scores.values())
        report = dict(metrics=scores, actions={arm: value[2] for arm, value in result.items()})
        if use_language:
            transport = {name: s.ledger_metrics(d, pair[0], mapping, costs) for name, pair in result.items()}
            assert all(abs(m["net"]-scores[name]["net"]) < 1e-9 for name, m in transport.items())
            report["language"] = transport
        return report

    rounds = {}
    for mode, balanced in (("balanced", True), ("uniform-stress", False)):
        rounds[mode] = {}
        for group in ("space-reserved", "mali", "myanmar"):
            if group == "space-reserved":
                rows = [dict(case=draw, **replay(setup(draw), balanced, True)) for draw in reserved]
                if balanced:
                    for row in rows:
                        prior = previous["evaluation"]["balanced"]["held"][str(row["case"])]["0.03"]
                        assert abs(row["metrics"]["frozen"]["net"]-prior["metrics"]["joint-fitted"]["net"]) < 1e-9
            else:
                rows = [dict(order=order, **replay(shared.Grid(group, order), balanced, False))
                        for order in permutations(range(3))]
            macro = {name: {m: mean(row["metrics"][name][m] for row in rows)
                            for m in ("net", "peer_rate", "after_followup")}
                     for name in rows[0]["metrics"]}
            rounds[mode][group] = dict(macro=macro, conditions=rows)
    from hashlib import sha256
    files = (Path(__file__), HERE / "recipient-protocol.md", HERE / "joint-opener.json", s.FIT, s.PROSE, s.original.REGISTRY)
    return dict(weights=coef.tolist(), training=training_stats, results=rounds,
                hashes={str(p.relative_to(s.SPACE.parents[1])): sha256(p.read_bytes()).hexdigest() for p in files})


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
