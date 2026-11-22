"""Adapt among frozen local routing policies using only public receipts."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

import facilitator_channel_fit as fit

EVIDENCE = fit.HERE / "facilitator-channel-online-evidence"
EPISODES = 144
PHASE = 48
REPLICAS = 128
SEED = 2593
RESET = .04
PROBE_EVERY = 8
HYPOTHESES = (fit.PERFECT, fit.channel(.95, .50, 1.), fit.channel(.70, .10, 1.), fit.channel(.35, .10, 1.))
OPTIONS = ("independent", "clean_fit", "initial_clean", "initial_noisy")


def joint(tail, opening, admission):
    q, reply = tail
    end = np.einsum("rbm,mt,rbtc->mtc", opening, fit.heard(fit.D.one_hot(q)), fit.D.one_hot(reply))
    good = np.sum(end * admission, axis=1)
    rejected = np.sum(end * (1 - admission), axis=(1, 2))
    joint = np.einsum("mc,mcn->mn", good, fit.D.LAST) + np.diag(rejected)
    assert np.allclose(joint.sum(1), opening.sum((0, 1)), atol=1e-12, rtol=0)
    return joint


def outcome_model(tails, opener, opening, prior, public, hypothesis):
    distributions, values = [], []
    for tail in tails:
        evidence = joint(tail, opening, hypothesis)
        metric = fit.measure(tail, opener, opening, prior, public, hypothesis)
        assert np.allclose(evidence.sum(0), metric["receipt_mass"], rtol=0, atol=1e-12)
        distributions.append(evidence)
        values.append(metric["net"])
    return np.asarray(distributions), np.asarray(values)


def choices(clean, public, opening):
    return (fit.exact(public, opening, fit.DESIGN, independent=True),
            fit.action_policy(clean, public, opening, fit.PERFECT),
            fit.action_policy(fit.OLD.INITIAL, public, opening, fit.PERFECT),
            fit.action_policy(fit.OLD.INITIAL, public, opening, fit.DESIGN))


def score_steps(observed, requests, actual, belief, options):
    windows = []
    for start in range(0, EPISODES, PHASE):
        sl = slice(start, start + PHASE)
        window = observed[:, sl]
        windows.append({"net": float(window.mean()), "requests": float(requests[:, sl].mean()),
                        "choices": dict(zip(OPTIONS, (np.bincount(options[:, sl].ravel(), minlength=len(OPTIONS))
                                                           / window.size).tolist(), strict=True)),
                        "mean_clean_posterior": float(belief[:, sl].mean()),
                        "last_clean_posterior": float(belief[:, start + PHASE - 1].mean()),
                        "actual_state": int(actual[start])})
    return {"mean_net": float(observed.mean()), "expected_total_net": float(observed.sum(1).mean()),
            "mean_requests": float(requests.mean()), "phases": windows}


def information(probabilities, likelihood):
    # KL between the hypothesized joint receipt distributions and the
    # current posterior predictor. The opening marginal is shared.
    marginal = np.einsum("rh,hkmn->rkmn", probabilities, likelihood)
    logs = np.log(np.maximum(likelihood, 1e-300))
    predictive_logs = np.log(np.maximum(marginal, 1e-300))
    return (np.einsum("rh,hkmn,hkmn->rk", probabilities, likelihood, logs)
            - np.sum(marginal * predictive_logs, axis=(2, 3)))


def online(likelihood, public_values, kernels, true_values, schedule, draws, opening_mass, rates, probe):
    posterior = np.full((REPLICAS, len(HYPOTHESES)), 1 / len(HYPOTHESES))
    nets = np.zeros((REPLICAS, EPISODES))
    used = np.empty_like(nets, dtype=int)
    probabilities, asks = np.zeros_like(nets), np.zeros_like(nets)
    opening_cdf = np.cumsum(opening_mass)
    after_opening = np.divide(kernels, opening_mass[None, None, :, None], out=np.zeros_like(kernels),
                              where=opening_mass[None, None, :, None] > 0.)
    receipt_cdf = np.cumsum(after_opening, axis=-1)
    for time, actual in enumerate(schedule):
        predicted = (1 - RESET) * posterior + RESET / len(HYPOTHESES)
        if probe and (time + 1) % PROBE_EVERY == 0:
            utility = information(predicted, likelihood)
        else:
            utility = predicted @ public_values
        policy = (utility + (len(OPTIONS) - np.arange(len(OPTIONS))) * 1e-12).argmax(1)
        before = np.minimum((draws[:, time, :1] > opening_cdf).sum(1), 7)
        after = np.minimum((draws[:, time, 1:2] > receipt_cdf[actual, policy, before]).sum(1), 7)
        assert np.all(before & after == before)
        update = predicted * likelihood[:, policy, before, after].T
        mass = update.sum(1, keepdims=True)
        posterior = np.divide(update, mass, out=predicted.copy(), where=mass > 0.)
        assert np.allclose(posterior.sum(1), 1.)
        used[:, time] = policy
        nets[:, time] = true_values[actual, policy]
        asks[:, time] = rates[policy]
        probabilities[:, time] = posterior[:, 0]
    return score_steps(nets, asks, schedule, probabilities, used)


def constant(values, schedule, rates, policy=None):
    states = values[schedule]
    selected = states.argmax(1) if policy is None else np.full(EPISODES, policy)
    selected_net = states[np.arange(EPISODES), selected]
    records = []
    for start in range(0, EPISODES, PHASE):
        end = start + PHASE
        records.append({"net": float(selected_net[start:end].mean()), "requests": float(rates[selected[start:end]].mean()),
                        "choice": OPTIONS[selected[start]], "actual_state": int(schedule[start])})
    return {"mean_net": float(selected_net.mean()), "expected_total_net": float(selected_net.sum()),
            "mean_requests": float(rates[selected].mean()), "phases": records}


def panel(clean, public, observed, prior, actual_modes, draws):
    opener, opening = fit.context(public, prior)
    mass = opening.sum((0, 1))
    tails = choices(clean, public, opening)
    likelihood, public_values = map(np.asarray, zip(*(outcome_model(tails, opener, opening, prior, public, h)
                                                       for h in HYPOTHESES), strict=True))
    kernels, true_values = map(np.asarray, zip(*(outcome_model(tails, opener, opening, prior, observed, h)
                                                  for h in actual_modes), strict=True))
    rates = np.array([mass @ (q != 0) for q, _ in tails])
    separability = np.abs(kernels[1:] - kernels[0]).sum(axis=(2, 3)) / 2.
    out = {}
    schedules = {"stable_clean": (0, 0, 0), "stable_noisy": (1, 1, 1), "changes": (0, 1, 0)}
    if len(actual_modes) > 2:
        schedules["stable_asymmetric"] = (2, 2, 2)
    for name, phases in schedules.items():
        schedule = np.repeat(phases, PHASE)
        out[name] = {
            "greedy_receipts": online(likelihood, public_values, kernels, true_values, schedule, draws, mass, rates, False),
            "active_receipts": online(likelihood, public_values, kernels, true_values, schedule, draws, mass, rates, True),
            "fixed_independent": constant(true_values, schedule, rates, policy=0),
            "fixed_clean_fit": constant(true_values, schedule, rates, policy=1),
            "oracle_in_menu": constant(true_values, schedule, rates),
        }
    return {"rates": dict(zip(OPTIONS, rates.tolist(), strict=True)),
            "clean_noisy_total_variation": separability.tolist(),
            "net_by_actual_mode": true_values.tolist(), "schedules": out}


def run(fitted):
    clean = json.loads(fitted.read_text())["clean"]
    observed_channel, _ = fit.measured_afghanistan()
    banks = fit.OLD.base.cases()[1]
    banks["resolution_2593"] = (fit.live.rubric(), fit.live.rubric())
    rng = np.random.default_rng(SEED)
    draws = rng.random((REPLICAS, EPISODES, 2))
    results = {}
    for family, (public, observed) in banks.items():
        actual = ((fit.PERFECT, observed_channel) if family == "resolution_2593" else
                  (fit.PERFECT, fit.STRESS["fallback_loss"], fit.STRESS["topic_asymmetry"]))
        results[family] = {label: panel(clean, public, observed, fit.ROUTE.TEST_PRIORS[label], actual, draws)
                           for label in fit.live.PRIORS}
    paths = (Path(__file__), EVIDENCE / "protocol.md", Path(fit.__file__), fitted,
             fit.live.EVIDENCE / "results.json")
    return {"episodes": EPISODES, "phase_length": PHASE, "replicas": REPLICAS, "seed": SEED, "reset": RESET,
            "probe_every": PROBE_EVERY, "hypotheses": [h.tolist() for h in HYPOTHESES],
            "options": OPTIONS, "results": results,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in paths}}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("fit_report", type=Path)
    print(json.dumps(run(cli.parse_args().fit_report), indent=2))
