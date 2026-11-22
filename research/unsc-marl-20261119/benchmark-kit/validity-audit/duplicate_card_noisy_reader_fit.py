"""Optimize decentralized coordination for an unreliable semantic reader."""
from hashlib import sha256
from itertools import product
import json
import sys

import numpy as np

from duplicate_card_semantic_review import EVIDENCE, MASKS, MESSAGE_COST, RECEIPT, SIGNAL_COST, mask_weight
from duplicate_card_semantic_sensitivity import ACTIONS, INVENTORIES, independent_readers

POLICY = EVIDENCE / "buffered-fit.json"
TRAINING_INPUT = EVIDENCE / "language/reward-fit.json"
SOURCE_PRIORS = EVIDENCE / "dprk-routes.json"
ANNOUNCEMENTS = tuple(product((0,), (0,), (0, 1), (0, 1)))
RESPONSES = np.asarray(list(product(ACTIONS, repeat=2)))
OBSERVATIONS = np.arange(len(INVENTORIES))
LEFT, RIGHT = INVENTORIES.T
PAIR = RECEIPT == 3
ATTEMPT = np.arange(3) > 0
DELIVERY_COST = MESSAGE_COST * np.add.outer(ATTEMPT.astype(int), ATTEMPT)
TRAIN_READERS = ((.10, .25), (.25, .10), (.20, .20))
TRAIN_LOSS = .15
SHIFTED_TRAINING = (
    {"marginals": ((.08, .48, .20, .24), (.10, .18, .46, .26)), "noise": (.32, .08), "loss": .22},
    {"marginals": ((.16, .58, .12, .14), (.20, .13, .53, .14)), "noise": (.07, .34), "loss": .27},
    {"marginals": ((.11, .20, .45, .24), (.13, .46, .17, .24)), "noise": (.28, .12), "loss": .18},
)


def weighted_payoff(worlds, gain, card_loss):
    # Keep true inventories latent. Compute the weight of warranted
    # deliveries conditional on the observations used by the policies.
    observed = worlds.sum(axis=0)
    deliverable = np.arange(3)[:, None] & INVENTORIES.T[:, None, :]
    eligible = deliverable == np.arange(3)[None, :, None]
    pair_mass = np.einsum("ia,ja,ao->oij", eligible[0], eligible[1], worlds)
    matrix = gain * (1 - card_loss) ** 2 * PAIR[None] * pair_mass - observed[:, None, None] * DELIVERY_COST
    return observed, matrix


def values(observed, matrix, signal_loss, announcement):
    bits = (np.asarray(announcement[0])[LEFT], np.asarray(announcement[1])[RIGHT])
    totals = np.zeros((len(RESPONSES), len(RESPONSES)))
    for keep in MASKS:
        left = RESPONSES[:, bits[1] * keep[0], LEFT]
        right = RESPONSES[:, bits[0] * keep[1], RIGHT]
        totals += mask_weight(keep, signal_loss) * matrix[OBSERVATIONS, left[:, None], right[None, :]].sum(axis=-1)
    return totals - SIGNAL_COST * (observed @ (bits[0] + bits[1]))


def compile_table(announcement, pair):
    table = np.zeros((2, 4, 5), dtype=int)
    for seat, rule in enumerate(announcement):
        bit = np.asarray(rule)
        table[seat, :, 0] = bit
        for peer in range(2):
            table[seat, np.arange(4), 1 + 2 * bit + peer] = RESPONSES[pair[seat], peer]
    return table


def optimize(scenarios):
    zero = (ANNOUNCEMENTS[0],) * 2
    silent = [values(*s, zero) for s in scenarios]
    # The silent comparator is given the same observation noise and prior.
    silent_best = np.array([v.max() for v in silent])
    best = {}
    for announcement in product(ANNOUNCEMENTS, repeat=2):
        result = np.stack(silent if announcement == zero else [values(*s, announcement) for s in scenarios])
        objectives = {"mean": result.mean(axis=0),
                      "worst_gain": (result - silent_best[:, None, None]).min(axis=0)}
        for mode, objective in objectives.items():
            pair = np.unravel_index(objective.argmax(), objective.shape)
            value = objective[pair]
            if mode not in best or value > best[mode]["objective"] + 1e-10:
                best[mode] = {"objective": float(value), "returns": result[:, *pair].tolist(),
                              "table": compile_table(announcement, pair)}
    return best, silent_best


def evaluate(table, worlds, loss, gain):
    observed, matrix = weighted_payoff(worlds, gain, loss)
    a, b = table[0, LEFT, 0], table[1, RIGHT, 0]
    score = -SIGNAL_COST * (observed @ (a + b))
    invalid = 0.
    for keep in MASKS:
        x = table[0, LEFT, 1 + 2 * a + b * keep[0]]
        y = table[1, RIGHT, 1 + 2 * b + a * keep[1]]
        weight = mask_weight(keep, loss)
        score += weight * matrix[OBSERVATIONS, x, y].sum()
        bad = ((x & LEFT[:, None]) != x) | ((y & RIGHT[:, None]) != y)
        invalid += weight * (worlds * bad).sum()
    return {"net": float(score), "unsupported_attempt_probability": float(invalid)}


def evaluation_cases():
    sources = json.loads(SOURCE_PRIORS.read_text())["arms"]
    for name, worlds in sources.items():
        prior = [row["probability"] for row in worlds["silent"]["worlds"]]
        for noise in ("clean", "symmetric", "overaccepts", "overrejects", "correlated"):
            if noise == "correlated":
                world = .5 * independent_readers(prior, .0, .0) + .5 * independent_readers(prior, .50, .50)
            else:
                fp, fn = {"clean": (0., 0.), "symmetric": (.30, .30),
                          "overaccepts": (.40, .05), "overrejects": (.05, .40)}[noise]
                world = independent_readers(prior, fp, fn)
            for loss_tag, loss in (("both_10", .10), ("both_25", .25)):
                yield name, noise, loss_tag, world, loss


def run(mixed_priors=False):
    archived = json.loads(POLICY.read_text())
    prior = json.loads(TRAINING_INPUT.read_text())["training_prior"]
    cases = [(*weighted_payoff(independent_readers(prior, fp, fn), 7, TRAIN_LOSS), TRAIN_LOSS)
             for fp, fn in TRAIN_READERS]
    if mixed_priors:
        for s in SHIFTED_TRAINING:
            shifted_prior = np.outer(*s["marginals"]).flatten()
            posterior = independent_readers(shifted_prior, *s["noise"])
            cases.append((*weighted_payoff(posterior, 7, s["loss"]), s["loss"]))
    trained, training_silent = optimize(cases)
    proof = np.array(archived["trained_tables"]["matched"])
    held_out = {}
    for name, noise, loss_tag, world, loss in evaluation_cases():
        stack = [(*weighted_payoff(world, 14., loss), loss)]
        bound, silent = optimize(stack)
        result = {label: evaluate(fit["table"], world, loss, 14.) for label, fit in trained.items()}
        result["prior_frozen"] = evaluate(proof, world, loss, 14.)
        assert all(r["net"] <= bound["mean"]["objective"] + 1e-9 for r in result.values())
        for r in result.values():
            r["gain_over_same_reader_silent"] = r["net"] - float(silent[0])
        result["exact_silent"] = float(silent[0])
        result["exact_communicating"] = bound["mean"]["objective"]
        if noise == "clean":
            previous = archived["priors"][name][loss_tag]
            assert np.isclose(result["exact_silent"] + 35, previous["exact_buffered_silent"]["net"])
            assert np.isclose(result["exact_communicating"] + 35, previous["exact_buffered_optional"]["net"])
        held_out.setdefault(name, {}).setdefault(noise, {})[loss_tag] = result
    report = {"scope": "Exact synthetic team-reward optimization under modeled reader errors. "
                     "The learned tables use only the locally predicted inventory and the peer bit.",
            "costs_subtracted": True, "training_readers": TRAIN_READERS, "training_loss": TRAIN_LOSS,
            "training_silent": training_silent.tolist(),
            "fit": {mode: {**entry, "table": entry["table"].tolist()} for mode, entry in trained.items()},
            "evaluation": held_out, "input_hashes": {p.name: sha256(p.read_bytes()).hexdigest()
                                                  for p in (POLICY, TRAINING_INPUT, SOURCE_PRIORS)}}
    if mixed_priors:
        report["shifted_training_scenarios"] = SHIFTED_TRAINING
    return report


if __name__ == "__main__":
    if sys.argv[1:] not in ([], ["--mixed-priors"]):
        raise SystemExit("usage: duplicate_card_noisy_reader_fit.py [--mixed-priors]")
    print(json.dumps(run(bool(sys.argv[1:])), indent=2))
