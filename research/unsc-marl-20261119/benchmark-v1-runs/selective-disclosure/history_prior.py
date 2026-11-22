"""Adapt a frozen recipient from unlabeled histories of local observations."""
from collections import defaultdict
from fractions import Fraction
from hashlib import sha256
import json
from statistics import mean
from unittest.mock import patch

import numpy as np
import torch

import joint_opener as opener
import ranking
import recipient
import selective as s

HERE, shared, base = s.HERE, s.shared, s.base
HORIZONS = (0, 4, 16, 32)
MODES = ("balanced", "uniform")
DENOMINATOR = 100_000


def mass_distribution(tables, with_peer):
    profiles = defaultdict(lambda: [Fraction(), Fraction()])
    for mode, doc in enumerate(tables):
        for key, row in doc.items():
            observation = key[1:] if with_peer else key[1]
            rational = Fraction(row["weight"]).limit_denominator(DENOMINATOR)
            assert abs(float(rational)-row["weight"]) < 1e-12
            profiles[observation][mode] += rational
    assert all(sum(r[i] for r in profiles.values()) == 1 for i in range(2))
    assert all(a > 0 and b > 0 for a, b in profiles.values())
    return profiles


def likelihoods(distribution):
    outcomes = defaultdict(lambda: np.zeros(2))
    for a, b in distribution.values():
        outcomes[a/b] += np.array([float(a), float(b)])
    states = {Fraction(1): np.ones(2)}
    saved = {}
    for step in range(max(HORIZONS)+1):
        if step in HORIZONS:
            keys = sorted(states)
            probs = np.stack([states[k] for k in keys])
            assert np.allclose(probs.sum(0), 1.)
            # Verify that the history's likelihood agrees with the indexed ratio.
            assert np.allclose(probs[:, 0], probs[:, 1]*np.asarray([float(r) for r in keys]))
            saved[step] = (np.array([float(k/(k+1)) for k in keys]), probs)
        if step < max(HORIZONS):
            delayed = defaultdict(lambda: np.zeros(2))
            for prev, mass in states.items():
                for observed, chance in outcomes.items():
                    delayed[prev*observed] += mass*chance
            states = delayed
    return saved, len(outcomes)


def forecasts(tables, prior_rows):
    states = sorted(tables[0], key=str)
    assert set(states) == set(tables[1])
    tensor = np.asarray([[[*table[k]["true"]] for k in states] for table in tables])
    probs = np.asarray([[table[k]["weight"] for k in states] for table in tables])
    utility = tensor*probs[:, :, None]
    pay = [row["peer_rate"]*base.FEE for row in prior_rows]

    def action(post):
        expected = post[:, None, None]*utility[0] + (1-post[:, None, None])*utility[1]
        optimal = expected.argmax(axis=2)
        output = np.zeros((len(post), 2))
        for i in range(2):
            output[:, i] = utility[i][np.arange(len(states)), optimal].sum(axis=1)-pay[i]
        return output

    oracle = action(np.array([1., 0.])).diagonal()
    return action, oracle


def adapt(priors, infos, dists):
    fixed, fitted = (np.array([row[name]["net"] for row in priors]) for name in ("fixed", "rank-fit"))
    values, oracle = forecasts(infos, [row["fixed"] for row in priors])
    target = np.array([row["exact-recipient"]["net"] for row in priors])
    assert np.allclose(oracle, target)

    def run(channel):
        histories, unique = likelihoods(dists[channel])
        results = {}
        for n, (posterior, mass) in histories.items():
            adaptive = np.where((posterior > .5)[:, None], fitted, fixed)
            choice = np.where((posterior*(fitted[0]-fixed[0]) + (1-posterior)*(fitted[1]-fixed[1]) > 1e-12)
                              [:, None], fitted, fixed)
            options = {
                "fixed": np.tile(fixed, (len(posterior), 1)),
                "rank": np.tile(fitted, (len(posterior), 1)),
                "posterior-switch": adaptive,
                "model-candidate": choice,
                "posterior-planner": values(posterior),
            }
            metrics = {name: dict(zip(MODES, (mass*row).sum(0).tolist(), strict=True)) for name, row in options.items()}
            metrics["declared-prior"] = dict(zip(MODES, oracle.tolist(), strict=True))
            for outcomes in metrics.values():
                outcomes["equal-mixture"] = mean(outcomes[k] for k in MODES)
            cap = metrics["posterior-planner"]["equal-mixture"]
            assert all(m["equal-mixture"] <= cap+1e-10 for name, m in metrics.items() if name != "declared-prior")
            results[n] = dict(accuracy=float(mass.max(1).sum()*.5), distinct_history_ratios=len(posterior),
                              policies=metrics)
        return dict(unique_observation_ratios=unique, horizons=results)

    return {channel: run(channel) for channel in dists}


def run():
    torch.set_num_threads(1)
    registry = s.read(s.original.REGISTRY)
    lookup = {r["draw"]: r for r in registry["accepted"]}
    w = torch.tensor(s.read(s.FIT)["weights"], dtype=torch.float64)
    op = np.asarray(s.read(HERE / "joint-opener.json")["weights"])
    ranked = s.read(HERE / "ranking.json")
    rank = np.asarray(ranked["coef"])
    value = np.asarray(s.read(HERE / "recipient.json")["weights"])

    def grid_from(draw):
        with patch.dict(shared.FIXTURES, {"target": s.original.fixture(lookup[draw])}):
            return shared.Grid("target")

    def stage(grid, balanced):
        d = shared.Experiment(grid, balanced)
        for i, role in enumerate(d.roles):
            if role == 2:
                d.mask[i, 1:] = False
        initial = d.probabilities(w).numpy()
        policy = opener.choose(d, initial, opener.basis(d, d.prior, initial), op, base.FEE, "joint-fitted")
        table = recipient.aggregate(d, policy)
        choices = ranking.measure(d, policy, table, rank, value)
        return d, choices, table

    cases = {f"space-{draw}": grid_from(draw) for draw in registry["partition"]["reserved"]}
    cases.update({key: shared.Grid(key) for key in ("mali", "myanmar")})
    output = {}
    for key, grid in cases.items():
        left, right = (stage(grid, balanced) for balanced in (True, False))
        assert left[0].states == right[0].states
        for arm in ("fixed", "rank-fit"):
            assert np.array_equal(left[1][arm][0], right[1][arm][0])
        scores = [{arm: r[1] for arm, r in row[1].items()} for row in (left, right)]
        for mode, score in zip(("balanced", "uniform-stress"), scores, strict=True):
            group = ranked["results"][mode]["mali" if key == "mali" else "myanmar" if key == "myanmar" else "space-reserved"]
            saved = next(r for r in group["rows"] if ("case" not in r or f"space-{r['case']}" == key))
            for arm in score:
                assert abs(score[arm]["net"] - saved["scores"][arm]["net"]) < 1e-9
        tables = [left[2], right[2]]
        dists = {channel: mass_distribution(tables, peer) for channel, peer in (("own", False), ("own+messages", True))}
        rows = adapt(scores, tables, dists)
        tv = {name: float(sum(abs(a-b) for a,b in dist.values())/2) for name, dist in dists.items()}
        assert tv["own+messages"]+1e-10 >= tv["own"]
        output[key] = dict(one_observation_tv=tv, history=rows)
    inputs = (HERE / "history-prior-protocol.md", HERE / "ranking.json", HERE / "joint-opener.json", s.original.REGISTRY)
    return dict(pins={p.name: sha256(p.read_bytes()).hexdigest() for p in inputs}, cases=output)


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
