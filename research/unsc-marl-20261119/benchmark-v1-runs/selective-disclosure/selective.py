"""Fit a targeted send gate from exact downstream workshop credit."""
from itertools import product
import json
from pathlib import Path
from statistics import mean
import sys
from unittest.mock import patch

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
SPACE = HERE.parents[1] / "crossbench/space"
sys.path.insert(0, str(SPACE))
import three_seat_positive_fit as original
import three_seat_language_score as language

shared, base = original.shared, original.base
FIT = SPACE / "evidence/three-seat-positive-fit.json"
PROSE = SPACE / "three-seat-language-contract-evidence/results.json"
FEES = (.015, .03, .06, .10)
POLICIES = ("original", "always", "never", "uniform-forecast", "fitted", "exact-gate")


def read(path):
    return json.loads(path.read_text())


def variant(grid, states, policy):
    """Evaluate both possible peer views separately for each hidden world."""
    values = {}
    for world in grid.worlds:
        for col in range(3):
            first = grid.claim(world, 0, col)
            payoff = []
            for view in (None, first):
                b = policy[states[("B", world[1], view)], :3]
                outcome = 0.
                for choice, chance in enumerate(b):
                    second = grid.claim(world, 1, choice)
                    for got_a, got_b in product((False, True), repeat=2):
                        receipt = (first if got_a else None, second if got_b else None)
                        rho = (base.DELIVER if got_a else 1-base.DELIVER) * (
                            base.DELIVER if got_b else 1-base.DELIVER)
                        possibilities, warranted = grid.information(receipt)
                        assert world in possibilities and warranted <= grid.winners(world)
                        outcome += chance*rho*bool(warranted)
                payoff.append(outcome)
            values[world, col] = payoff
    return values


def summarize(d, policy):
    # Access to the recipient at each permitted observation is frozen at deployment.
    grid = d.grid
    values = variant(grid, d.states, policy)
    prior = d.prior
    info = {}
    for i in range(len(grid.cards[0])):
        present = [w for w in grid.worlds if w[0] == i]
        reach = sum(prior[w] for w in present)
        options = []
        for col in range(3):
            raw = [values[w, col][1]-values[w, col][0] for w in present]
            uniform = base.PEER*mean(raw)
            balanced = base.PEER*sum(prior[w]*x for w, x in zip(present, raw, strict=True))/reach
            grade, _, uncertainty, cert, remainder, *_ = grid.counsel(0, i, col, None)
            # The correction sees the public local features and a same-budget forecast.
            features = (1., uniform, grade, uncertainty, cert, remainder, float(grade == 0))
            prob = sum(policy[d.states[("A", i)], 2*col:2*col+2])
            options.append(dict(features=features, uniform=uniform, exact=balanced, weight=reach*prob))
        info[i] = options
    assert abs(sum(o["weight"] for opts in info.values() for o in opts)-1.) < 1e-9
    return info


def fit(tables):
    samples = [value for one in tables for opts in one.values() for value in opts]
    x = np.array([row["features"] for row in samples])
    baseline = np.array([row["uniform"] for row in samples])
    target = np.array([row["exact"] for row in samples])
    relevance = np.sqrt([row["weight"] for row in samples])
    penalty = .02 * np.eye(x.shape[1])
    design = x * relevance[:, None]
    coef = np.linalg.solve(design.T@design + penalty, design.T@((target-baseline)*relevance))
    return coef, {
        "samples": len(samples), "residual_weighted_rmse": float(np.linalg.norm((x@coef+baseline-target)*relevance) / np.linalg.norm(relevance)),
        "uniform_weighted_rmse": float(np.linalg.norm((baseline-target)*relevance) / np.linalg.norm(relevance)),
    }


def gated(d, start, table, coef, name, fee):
    p = start.copy()
    if name == "original":
        return p
    for i, choices in table.items():
        row = d.states["A", i]
        for col, value in enumerate(choices):
            prob = sum(start[row, 2*col:2*col+2])
            rule = {"always": 1., "never": 0., "uniform-forecast": value["uniform"],
                    "fitted": value["uniform"]+float(np.asarray(value["features"])@coef),
                    "exact-gate": value["exact"]}
            k = int(rule[name] > fee)
            p[row, 2*col:2*col+2] = 0.
            p[row, 2*col+k] = prob
    assert np.allclose(start.sum(axis=1), p.sum(axis=1))
    return p


def measure(d, policy, rate):
    score = d.metrics(policy)
    score["net"] += (base.FEE-rate) * score["peer_rate"]
    return score


def ledger_metrics(d, start, mapping, costs):
    m = language.projection(d, start, mapping, "bound", costs)
    assert m["unsupported_certificate"] == m["false_certificate"] == 0.
    m["charged_fee"] = base.FEE
    return m


def evaluate(d, start, info, coef, saved, mapping, cost):
    out = {}
    for rate in FEES:
        projections = {}
        measures = {}
        for name in POLICIES:
            p = gated(d, start, info, coef, name, rate)
            outcome = measure(d, p, rate)
            if rate == base.FEE:
                scores = ledger_metrics(d, p, mapping, cost)
                assert abs(scores["net"] - outcome["net"]) < 1e-9
                projections[name] = scores
            measures[name] = outcome
        assert all(m["net"] <= measures["exact-gate"]["net"] + 1e-9 for m in measures.values())
        result = {"measures": measures}
        if rate == base.FEE:
            assert abs(measures["original"]["net"] - saved["fitted"]["net"]) < 1e-9
            result["exact_independent"] = saved["exact_independent"]
            result["exact_peer"] = saved["exact_peer"]
            for m in measures.values():
                assert m["net"] <= saved["exact_peer"]["net"] + 1e-9
            result["language"] = projections
        out[rate] = result
    return out


def run():
    torch.set_num_threads(1)
    registry = read(original.REGISTRY)
    archived = read(FIT)
    index = {row["draw"]: row for row in registry["accepted"]}
    from hashlib import sha256
    assert archived["registry_sha256"] == sha256(original.REGISTRY.read_bytes()).hexdigest()
    fit_ids, test_ids = (registry["partition"][k] for k in ("fit", "reserved"))
    assert not set(fit_ids) & set(test_ids)
    w = torch.as_tensor(archived["weights"], dtype=torch.float64)
    prose = read(PROSE)
    assert prose["confirmed_declarations"] == 12 and len(prose["messages"]) == 12
    mapping = {tuple(r["intended"]): tuple(r["evidence_reader"]) for r in prose["messages"]}
    assert all(k == v for k, v in mapping.items())
    costs = {tuple(r["intended"]): (r["tokens"]["writer"], r["tokens"]["evidence"]) for r in prose["messages"]}

    def lane(idx):
        with patch.dict(shared.FIXTURES, {"target": original.fixture(index[idx])}):
            d = original.data_for(shared.Grid("target"))
        start = d.probabilities(w).numpy()
        info = summarize(d, start)
        return d, start, info

    coef, training = fit([lane(idx)[2] for idx in fit_ids])
    held = []
    gold = {row["grid_id"]: row["results"] for row in archived["reserved"]}
    for idx in test_ids:
        d, start, info = lane(idx)
        held.append(dict(grid=idx, values=info, eval=evaluate(d, start, info, coef, gold[idx], mapping, costs)))
    macro = {}
    for fee in FEES:
        macro[fee] = {arm: {key: mean(h["eval"][fee]["measures"][arm][key] for h in held)
                            for key in ("net", "after_followup", "peer_rate")} for arm in POLICIES}
    model_calls = {arm: {k: mean(row["eval"][base.FEE]["language"][arm][k] for row in held)
                          for k in ("uncached_model_calls", "uncached_generated_tokens")} for arm in POLICIES}
    files = (Path(__file__), HERE / "protocol.md", FIT, original.REGISTRY, PROSE)
    return dict(coef=coef.tolist(), training=training, held=held, macro=macro, language=model_calls,
                hashes={str(p.relative_to(SPACE.parents[1])): sha256(p.read_bytes()).hexdigest() for p in files})


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
