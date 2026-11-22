"""Distinguish peer erasure changes from prior shifts with exact passive histories."""
from collections import defaultdict
from fractions import Fraction
from itertools import product
from pathlib import Path
from statistics import mean
from unittest.mock import patch
import json

import numpy as np
import torch

import history_prior as history
import joint_opener as opener
import ranking
import recipient
import selective as s

HERE, shared, base = s.HERE, s.shared, s.base
HORIZONS = (0, 4, 16)
REGIMES = tuple(product((True, False), (.8, .4)))
REGIME_NAMES = tuple(f"{'balanced' if balanced else 'uniform'}/{link}" for balanced, link in REGIMES)
NOMINAL = (0, 2)


def world_profiles(data, opening, nom, rank, val):
    result = []
    for balanced, link in REGIMES:
        with patch.object(base, "PEER", link):
            d = shared.Experiment(data.grid, balanced)
            assert d.states == data.states
            for i, role in enumerate(d.roles):
                if role == 2:
                    d.mask[i, 1:] = False
            table = recipient.aggregate(d, opening)
            ranked = ranking.measure(d, opening, table, rank, val)
        if link == .8:
            for arm in ("fixed", "rank-fit"):
                assert np.array_equal(nom[arm][0], ranked[arm][0])
        result.append((table, ranked))
    assert all(set(row[0]) == set(result[0][0]) for row in result)
    return result


def observations(rows):
    keys = sorted(rows[0][0], key=str)
    rational = [[Fraction(entry[0][k]["weight"]).limit_denominator(history.DENOMINATOR) for k in keys]
                for entry in rows]
    assert all(sum(profile) == 1 and all(profile) for profile in rational)
    assert all(abs(float(p)-entry[0][key]["weight"]) < 1e-12
               for entry, profile in zip(rows, rational, strict=True)
               for p, key in zip(profile, keys, strict=True))
    groups = defaultdict(lambda: np.zeros(4))
    for raw in zip(*rational, strict=True):
        signature = tuple(p/raw[0] for p in raw[1:])
        groups[signature] += np.asarray([float(p) for p in raw])
    return keys, groups


def histories(distributions):
    splits = {(Fraction(1),)*3: np.ones(4)}
    for step in range(max(HORIZONS)+1):
        if step in HORIZONS:
            keys = sorted(splits)
            values = np.stack([splits[k] for k in keys])
            ratios = np.asarray([[1., *map(float, k)] for k in keys])
            assert np.allclose(values.sum(0), 1.)
            assert np.allclose(values, values[:, :1]*ratios)
            posterior = ratios/ratios.sum(axis=1, keepdims=True)
            naive = ratios[:, NOMINAL]
            naive /= naive.sum(axis=1, keepdims=True)
            yield step, values, posterior, naive
        if step < max(HORIZONS):
            following = defaultdict(lambda: np.zeros(4))
            for key, mass in splits.items():
                for likelihood, probability in distributions.items():
                    signature = tuple(a*b for a,b in zip(key, likelihood, strict=True))
                    following[signature] += mass*probability
            splits = following


def replay(rows, data, nom):
    deltas = {}
    keys, probabilities = observations(rows)
    harvest = np.array([[entry[0][k]["true"]*entry[0][k]["weight"] for k in keys] for entry in rows])
    fees = np.array([entry[1]["fixed"][1]["peer_rate"]*base.FEE for entry in rows])

    def deployment(action):
        expected = harvest[:, np.arange(len(keys)), action].sum(-1).T
        return expected-fees

    by_arm = {}
    for tag in ("rank-fit", "fixed"):
        choice = np.array([nom[tag][0][data.states[k], :3].argmax() for k in keys])
        by_arm[tag] = deployment(choice)
    target = np.array([entry[1]["exact-recipient"][1]["net"] for entry in rows])
    assert np.allclose(target, harvest.max(-1).sum(-1)-fees)
    assert np.all(by_arm["fixed"] <= target+1e-9) and np.all(by_arm["rank-fit"] <= target+1e-9)
    for n, mass, full, naive in histories(probabilities):
        aware = np.einsum("hk,ksa->hsa", full, harvest).argmax(-1)
        narrow = np.einsum("hk,ksa->hsa", naive, harvest[list(NOMINAL)]).argmax(-1)
        candidates = {"fixed": by_arm["fixed"], "rank-fit": by_arm["rank-fit"], "declared": target,
                      "joint-planner": deployment(aware), "nominal-link-planner": deployment(narrow)}
        values = {}
        for name, value in candidates.items():
            fragment = (mass*value).sum(0)
            values[name] = dict(zip(REGIME_NAMES, fragment.tolist(), strict=True)) | {"mean": float(fragment.mean())}
        assert values["joint-planner"]["mean"] <= values["declared"]["mean"] + 1e-10
        assert all(row["mean"] <= values["joint-planner"]["mean"]+1e-10 for k, row in values.items()
                   if k != "declared")
        deltas[n] = dict(metrics=values, unique_histories=len(mass), regime_accuracy=float(mass.max(1).sum()/4))
    return dict(observation_likelihoods=len(probabilities), history=deltas)


def run():
    torch.set_num_threads(1)
    registry = s.read(s.original.REGISTRY)
    lookup = {r["draw"]: r for r in registry["accepted"]}
    original = torch.tensor(s.read(s.FIT)["weights"], dtype=torch.float64)
    open_w = np.asarray(s.read(HERE / "joint-opener.json")["weights"])
    rank = np.asarray(s.read(HERE / "ranking.json")["coef"])
    val = np.asarray(s.read(HERE / "recipient.json")["weights"])

    def make(draw):
        with patch.dict(shared.FIXTURES, {"new": s.original.fixture(lookup[draw])}):
            return shared.Grid("new")

    grids = {f"space-{draw}": make(draw) for draw in registry["partition"]["reserved"]}
    grids.update({group: shared.Grid(group) for group in ("mali", "myanmar")})
    panels = {}
    for key, grid in grids.items():
        data = s.original.data_for(grid)
        frozen = data.probabilities(original).numpy()
        value = opener.basis(data, data.prior, frozen)
        opening = opener.choose(data, frozen, value, open_w, base.FEE, "joint-fitted")
        nominal = ranking.measure(data, opening, recipient.aggregate(data, opening), rank, val)
        panels[key] = replay(world_profiles(data, opening, nominal, rank, val), data, nominal)
    macro = {n: {arm: mean(row["history"][n]["metrics"][arm]["mean"] for key, row in panels.items()
                           if key.startswith("space-"))
                 for arm in panels["space-198"]["history"][n]["metrics"]} for n in HORIZONS}
    from hashlib import sha256
    pins = (Path(__file__), HERE / "history-link-protocol.md", HERE / "ranking.json", HERE / "joint-opener.json")
    return dict(cases=panels, reserved_macro=macro,
                hashes={p.name: sha256(p.read_bytes()).hexdigest() for p in pins})


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
