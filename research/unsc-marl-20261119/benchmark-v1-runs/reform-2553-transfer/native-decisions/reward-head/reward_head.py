"""Fit two role-local policies using shared payoff and frozen language margins."""
import argparse
import json
from itertools import product
from pathlib import Path
from statistics import mean
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parent
RUNS = HERE.parents[2]
PARTNER = RUNS / "cooperative-rollout-fit/evidence-choice/receipt-conditioned/partner-forecast"
sys.path.insert(0, str(NATIVE))
sys.path.insert(0, str(PARTNER))
import live_choices as native
import forecast_response as forecast

reform, READ, prior = native.case, native.READ, native.prior
receipt, old = forecast.receiver, forecast.old
MODES = ("content", "arrival", "none")
VIEWS = {"content": ("absent", "card1", "card2"), "arrival": ("absent", "arrived"), "none": ("none",)}
STEPS = 120
RATE = .18
PENALTY = .005
FIT_INPUTS = (Path(__file__), HERE / "protocol.md", NATIVE / "verified.json", NATIVE / "scores.json",
              NATIVE.parent / "results.json", Path(forecast.__file__), Path(receipt.__file__))


def margin(outputs, context):
    def read(mapping):
        row = outputs[f"{context}/{mapping}"]["logits"]
        return row["A"] - row["B"]
    delta = (read("ab") - read("ba")) / 2
    return np.array([delta / 2, -delta / 2])


def sample(local, edges, rate, share, true, outputs, prefix):
    scene = receipt.features((2, 2, 2), (1, 1, 1), local, edges, (rate,) * 3, true)
    shares = np.array([share, 1. - share])
    legacy, features, _ = forecast.design(scene, local, edges, (rate,) * 3, shares)
    a, c = features
    prior_a = shares @ a[1:].reshape(len(shares), -1)
    prior_a = prior_a.reshape(a[0].shape)
    obs = scene["observe"]
    views = {"content": (obs, a, legacy[0]),
             "arrival": ((obs > 0).astype(int), np.stack((a[0], prior_a)),
                         np.stack((legacy[0][0], np.einsum("b,baf->af", shares, legacy[0][1:])))),
             "none": (np.zeros_like(obs), ((1 - rate) * a[0] + rate * prior_a)[None, :, :],
                      ((1-rate) * legacy[0][0] + rate * np.einsum("b,baf->af", shares, legacy[0][1:]))[None,:,:])}
    probabilities = shares[:, None] * scene["mask_probabilities"][None, :]
    return {view: {"returns": scene["returns"], "p": probabilities, "obs": view_ids,
                   "features": (design, c), "legacy": (old_payload, legacy[1]),
                   "language": (np.stack([margin(outputs, f"{prefix}/{i}") for i in VIEWS[view]]),
                                margin(outputs, f"{prefix}/independent")),
                   "true_records": true}
            for view, (view_ids, design, old_payload) in views.items()}


def objective(sample_, weights, language=True):
    a, c = sample_["features"]
    qa, qc = sample_["language"]
    pa = np.stack([old.softmax(item) for item in a @ weights + language * qa])
    pc = old.softmax(c @ weights + language * qc)
    obs = sample_["obs"]
    mass = sample_["p"][:, None, :, None] * pc[None,:,None,None] * pa[obs][:,None,:,:]
    assert abs(mass.sum() - 1) <= 1e-9
    value = float(np.sum(mass * sample_["returns"]))
    residual = mass * (sample_["returns"] - value)
    conditional = (a - np.einsum("oa,oaf->of", pa, a)[:, None, :])[obs]
    gradient = np.einsum("bcma,bmaf->f", residual, conditional)
    gradient += np.einsum("bcma,cf->f", residual, c - pc @ c)
    return value, gradient


def training_set():
    log = READ(NATIVE / "verified.json")["outputs"]
    rows = {}
    for order, permutation in reform.ORDERS.items():
        _, local, edges, _, true = reform.setup(permutation)
        for rate in native.RATES:
            key = f"{order}/{rate}"
            rows[key] = sample(local, edges, rate, native.SHARE, true, log, key)
    return rows


def fit():
    rows = training_set()
    samples = [world for episodes in rows.values() for world in episodes.values()]
    assert len(samples) == 12
    output = {}
    for name, use_language in (("hybrid", True), ("typed_only", False)):
        weights = np.zeros(3)
        trace = []
        for step in range(STEPS + 1):
            results = [objective(world, weights, use_language) for world in samples]
            value = mean(r for r, _ in results)
            gradient = np.mean([delta for _, delta in results], axis=0) - PENALTY * weights
            if step == 0:
                eps = 1e-5
                approx = [(objective(samples[0], weights + axis * eps, use_language)[0] -
                           objective(samples[0], weights - axis * eps, use_language)[0]) / (2 * eps)
                          for axis in np.eye(3)]
                assert np.allclose(approx, results[0][1], atol=1e-7, rtol=0)
            if step % 15 == 0:
                trace.append({"update": step, "expected_reward_above_public": value,
                              "weights": weights.tolist()})
            if step < STEPS:
                weights += RATE * gradient
        assert trace[-1]["expected_reward_above_public"] >= trace[0]["expected_reward_above_public"]
        output[name] = trace
    return {"heads": output, "cases": list(rows), "steps": STEPS, "rate": RATE, "penalty": PENALTY,
            "sources": {str(p.relative_to(RUNS)): prior.digest(p) for p in FIT_INPUTS}}


def action_scores(sample_, frozen):
    later, third = sample_["features"]
    qa, qc = sample_["language"]
    legacy_a, legacy_c = sample_["legacy"]
    full = {"raw_qwen": (qa, qc), "local": (later[..., 0], third[..., 0]),
            "fixed_legacy": (legacy_a[..., 0] + legacy_a[..., 2], legacy_c[..., 0] + legacy_c[..., 2]),
            "fixed_refreshed": (later[..., 0] + later[..., 2], third[..., 0] + third[..., 2])}
    for name in ("hybrid", "typed_only"):
        w = np.asarray(frozen["heads"][name][-1]["weights"])
        enabled = name == "hybrid"
        full[name] = (later @ w + qa * enabled, third @ w + qc * enabled)
    def choose(logits, local):
        assert logits.shape == local.shape
        return np.where(logits[..., 0] == logits[..., 1], np.argmax(local, axis=-1), np.argmax(logits, axis=-1))
    return {name: (choose(a, later[..., 0]), int(choose(c, third[..., 0])))
            for name, (a, c) in full.items()}


def score(sample_, fit_):
    plans = action_scores(sample_, fit_)
    rewards, p, views = (sample_[key] for key in ("returns", "p", "obs"))
    optimum, action, last = forecast.replay.optimal(rewards, p, views)
    plans["oracle"] = np.asarray(action), last
    true = sample_["true_records"]
    public = true[(0, 0, 0)][0]
    outcomes = {}
    for arm, (a, c) in plans.items():
        checked = forecast.replay.expected(rewards, p, views, a, c)
        figure = sum(p[b, mask] * true[(a[views[b, mask]], b, c)][mask]
                     for b, mask in product(range(len(p)), range(8)))
        assert checked <= optimum + 1e-9 and abs(figure - checked - public) < 1e-9
        outcomes[arm] = {"released": float(figure), "later": a.tolist(), "third": c}
    return outcomes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("fit",))
    parser.parse_args()
    native.frozen.emit(fit())
