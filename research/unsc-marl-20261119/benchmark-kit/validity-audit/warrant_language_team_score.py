"""Replay the frozen adaptive chair against actual public report admissions."""
import argparse
import json
from pathlib import Path
import re

import numpy as np

import warrant_language_team as study

receiver = study.receiver
adapt = receiver.adapt
design, world = study.design, study.world
PACKAGES = world.two.PACKAGES


def reports(rows, index, cards, intended):
    observed = np.full((3, 4), -1, dtype=int)
    detail = {}
    for role, card_type in np.ndindex(3, 4):
        key = f"d{index}/D{role+1}/card{card_type}"
        row = rows[key]
        match = re.fullmatch(r"D([123]) reports grade ([0-3]) for ([ABC])\.", row["output"])
        if row["ended"] and match:
            speaker, grade, package = match.groups()
            slot = PACKAGES.index(package)
            if int(speaker) == role + 1 and int(grade) == cards[role, card_type, slot]:
                if role != 2 or slot == intended[role, card_type]:
                    observed[role, card_type] = slot
        detail[key] = {"raw": row["output"], "admitted": bool(observed[role, card_type] >= 0),
                       "intended_package": PACKAGES[intended[role, card_type]], "input_tokens": len(row["input_ids"]),
                       "output_tokens": len(row["output_ids"])}
    return observed, detail


def actual_values(task, p, table):
    intentions = table[np.arange(3), world.TYPES]
    slot = np.maximum(intentions, 0) @ np.array([9, 3, 1])
    observed = world.LINKS[None] & (intentions[:, None, :] >= 0)
    live_link = observed @ np.array([4, 2, 1])
    hidden = np.arange(64)[:, None]
    states = task.state[hidden, slot[:, None], live_link]
    weight = p[:, None] * world.P_LINKS
    amount = np.bincount(states.ravel(), weights=weight.ravel(), minlength=task.num_states)
    assert abs(amount.sum() - 1.) < 1e-12
    matrix = np.zeros((task.num_states, 10))
    np.add.at(matrix, states.ravel(),
              (weight[..., None] * task.pay[hidden, slot[:, None], live_link]).reshape(-1, 10))
    return matrix, amount


def metric(task, utility, occurrence, request):
    if request.ndim == 1:
        request = request[None]
    state = np.arange(task.num_states)
    assert task.legal[state, request].all()
    net = utility[state, request].sum(1)
    asked = (occurrence * (request != 0)).sum(1)
    return {"mean_net": float(net.mean()), "mean_certified": float((net + world.two.REPLY_COST * asked).mean()),
            "mean_requests": float(asked.mean())}


def predict(task, p, semantic_styles, utility, occurrence, draws):
    forecast, likelihood = adapt.models(task, p, semantic_styles, factor=True)
    ledger, support = receiver.flexible.registry(task)
    history = np.searchsorted(np.cumsum(occurrence), draws, side="right")
    assert np.all(occurrence[history] > 0.)
    grade_only = task.requests(task.weights(np.full((3, 4, 3), 1 / 3.), p))
    scores = {"grade_only": metric(task, utility, occurrence, grade_only),
              "partner_known": metric(task, utility, occurrence, design.choose(task, utility))}
    for n in (0, 4, 16):
        discrete = np.einsum("rh,hsa->rsa", adapt.posterior(likelihood, history[:, :n]), forecast)
        scores[f"role_factored/{n}"] = metric(task, utility, occurrence, design.choose(task, discrete))
    exponent = receiver.validation_discrete(likelihood, history)
    warm = ((1 - adapt.CONTAMINATION) *
            np.stack([np.eye(3)[semantic_styles[k]] for k in design.TRAIN_PARTNERS]).mean(0) +
            adapt.CONTAMINATION / 3.)
    preliminary = receiver.flexible.fit_histories(ledger, support, history[:, :receiver.PREFIX], p, warm)
    predictive = [design.returns(task, task.weights(params, p))[1] for params in preliminary]
    validation = np.log(np.asarray(predictive)[np.arange(len(history))[:, None], history[:, receiver.PREFIX:]]).sum(-1)
    weight = 1. / (1. + np.exp(-np.clip(validation - exponent, -700., 700.)))
    tail = receiver.flexible.fit_histories(ledger, support, history, p, warm)
    candidate = np.stack([design.returns(task, task.weights(params, p))[0] for params in tail])
    combined = (1 - weight[:, None, None]) * discrete + weight[:, None, None] * candidate
    scores["blend/16"] = {**metric(task, utility, occurrence, design.choose(task, combined)),
                          "mean_flexible_weight": float(weight.mean())}
    assert all(v["mean_net"] <= scores["partner_known"]["mean_net"] + 1e-12 for v in scores.values())
    return scores


def run(rows):
    rng = np.random.default_rng(adapt.SEED)
    result = []
    for i, cards in enumerate(study.domains()):
        task = world.Workshop(cards)
        styles = study.fitted(task)
        intended = styles["mixed"]
        actual, notes = reports(rows, i, cards, intended)
        scores = {}
        for label, correlated in (("uniform", False), ("correlated", True)):
            p = world.prior(correlated)
            draws = rng.random((adapt.REPLICAS, adapt.STEPS[-1]))
            scores[label] = {}
            for condition, table in (("language", actual), ("typed", intended)):
                u, f = actual_values(task, p, table)
                if condition == "typed" or (table >= 0).all():
                    expected = design.returns(task, task.weights(np.eye(3)[table], p))
                    assert np.allclose(u, expected[0], rtol=0., atol=1e-12)
                    assert np.allclose(f, expected[1], rtol=0., atol=1e-12)
                scores[label][condition] = predict(task, p, styles, u, f, draws)
        result.append({"domain": i, "cards": cards.tolist(), "intended": intended.tolist(),
                       "admitted_slots": actual.tolist(), "report_audit": notes, "scores": scores})
    return {"domains": result, "histories_per_condition": adapt.REPLICAS, "history_prefixes": [0, 4, 16]}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    print(json.dumps(run(study.verify(cli.parse_args().directory)), indent=2, ensure_ascii=False))
