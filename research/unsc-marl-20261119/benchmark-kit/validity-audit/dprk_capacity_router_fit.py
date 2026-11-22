"""Fit one router to jointly handle both observed availability regimes."""
import argparse
from itertools import product
import json
from pathlib import Path

import numpy as np

from dprk_capacity_route_review import STYLES, capacity_report, qualifier_report, readings
from duplicate_card_noisy_reader_fit import ANNOUNCEMENTS, compile_table, evaluate, values, weighted_payoff
from duplicate_card_semantic_review import EVIDENCE, PRIVATE, digest, reward_tables

TRAIN_STYLES = ("original_or_missing", "reordered_or_reversed")
LOSSES = (0., .1, .25)
NO_SIGNAL = (ANNOUNCEMENTS[0],) * 2


def worlds(prior, rows):
    # A submitted role has the same identity as its source family in this panel.
    mapping = []
    for inventory in range(4):
        observed = 0
        for card in (1, 2):
            present = bool(inventory & card)
            reading = rows["dprk", card, "positive" if present else "negative"]
            assert reading["truth"] == (card if present else 0)
            assert reading["span_model"] in (0, card)
            observed |= reading["span_model"]
        mapping.append(observed)
    law = np.zeros((len(PRIVATE), len(PRIVATE)))
    positions = {pair: i for i, pair in enumerate(PRIVATE)}
    for i, (left, right) in enumerate(PRIVATE):
        law[i, positions[mapping[left], mapping[right]]] += prior[i]
    assert np.isclose(law.sum(), 1)
    return law, mapping


def fit(scenarios):
    silent_values = [values(*case, NO_SIGNAL) for case in scenarios]
    silence = np.array([v.max() for v in silent_values])
    champion = None
    for announce in product(ANNOUNCEMENTS, repeat=2):
        returns = np.stack(silent_values if announce == NO_SIGNAL else [values(*case, announce) for case in scenarios])
        gains = returns - silence[:, None, None]
        worst = gains.min(axis=0)
        best_worst = worst.max()
        tied = np.isclose(worst, best_worst, atol=1e-10, rtol=0)
        mean = gains.mean(axis=0)
        pair = np.unravel_index(np.where(tied, mean, -np.inf).argmax(), mean.shape)
        this = (float(worst[pair]), float(mean[pair]))
        if (champion is None or this[0] > champion[0][0] + 1e-10
                or abs(this[0] - champion[0][0]) <= 1e-10 and this[1] > champion[0][1] + 1e-10):
            champion = (this, compile_table(announce, pair), gains[:, *pair].tolist())
    return champion


def report(capacity_dir):
    cap = capacity_report(capacity_dir)
    reason = qualifier_report(EVIDENCE / "qualifier-dprk")
    roll = json.loads((capacity_dir / "route-score.json").read_text())
    assert roll["capacity_probe_sha256"] == cap["actions_sha256"]
    assert roll["qualifier_probe_sha256"] == reason["actions_sha256"]
    japan = {r["case"]: r for r in cap["rows"]}
    china = {r["key"][2]: r for r in reason["passage_readings"] + reason["synthetic_scope_controls"]
             if r["key"][1] == 2}
    source_priors = EVIDENCE / "dprk-routes.json"
    priors = {k: [r["probability"] for r in v["silent"]["worlds"]]
              for k, v in json.loads(source_priors.read_text())["arms"].items()}
    maps = {key: readings(japan, china, variants, "reason_agreement") for key, variants in STYLES.items()}
    reward = reward_tables()["dprk"]
    public = reward[0, 0]
    gain = reward[1, 2] - public
    train = [(*weighted_payoff(worlds(priors["uniform"], maps[style])[0], gain, .1), .1)
             for style in TRAIN_STYLES]
    key, fitted, train_gain = fit(train)
    policy = EVIDENCE / "buffered-fit.json"
    frozen = np.asarray(json.loads(policy.read_text())["trained_tables"]["matched"])
    comparisons = []
    for style, prior, loss in product(STYLES, priors, LOSSES):
        law, mapping = worlds(priors[prior], maps[style])
        case = (*weighted_payoff(law, gain, loss), loss)
        silent = values(*case, NO_SIGNAL).max()
        value = evaluate(fitted, law, loss, gain)
        original = evaluate(frozen, law, loss, gain)
        audit = next(r for r in roll["evaluations"] if r["style"] == style and r["prior"] == prior
                     and r["loss"] == {0.: "none", .1: "both_10", .25: "both_25"}[loss]
                     and r["reader"] == "span_model" and r["china_rule"] == "reason_agreement")
        assert np.isclose(audit["optimal_silence"]["net"], public + silent)
        assert np.isclose(audit["learned"]["net"], public + original["net"])
        for y in (value, original):
            y["gain_over_silence"] = y["net"] - silent
            y["net"] += public
        comparisons.append({"style": style, "prior": prior, "loss": loss, "observed_masks": mapping,
                            "included_in_fit": style in TRAIN_STYLES and prior == "uniform" and loss == .1,
                            "refit": value, "frozen": original, "optimal_silence": float(public + silent)})
    return {
        "scope": "Exact team-reward optimization on two observed-reader development regimes. "
                 "Actor tables see only their reconstructed local evidence and the received availability bit. "
                 "The optimization has a gold receipt gate and uses archived downstream record values. "
                 "The new decoys share a routing observation map with the reordered training regime.",
        "training": {"styles": TRAIN_STYLES, "inventory_prior": "uniform", "loss": .1,
                     "reader": "span_model with unanimous China", "objective": "worst gain then mean gain",
                     "worst_gain": key[0], "mean_gain": key[1], "per_style_gain": train_gain,
                     "table": fitted.tolist()},
        "sources": {p.name: digest(p) for p in (source_priors, policy, capacity_dir / "route-score.json")},
        "comparison": comparisons,
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    print(json.dumps(report(cli.parse_args().directory), ensure_ascii=False, indent=2))
