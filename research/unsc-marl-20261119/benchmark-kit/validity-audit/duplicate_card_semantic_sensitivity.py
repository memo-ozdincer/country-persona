"""Measure the reading reliability needed for the buffered routing gain."""
import json
from itertools import product

import numpy as np

from duplicate_card_semantic_review import EVIDENCE, MASKS, MESSAGE_COST, PRIVATE, RECEIPT, SIGNAL_COST, mask_weight

LOSS = .10
GRID = (0., .10, .20, .30, .40, .50)
ACTIONS = np.asarray(list(product((0,), (0, 1), (0, 2), (0, 1, 2))))
INVENTORIES = np.array(PRIVATE)
BOOK = np.arange(4)[:, None] & [1, 2] != 0
ATTEMPT = np.arange(3) > 0
ACHIEVABLE = 14 * (1 - LOSS) ** 2


def independent_readers(prior, false_accept, false_reject):
    error = np.where(BOOK, false_reject, false_accept)
    scores = np.where(BOOK[:, None] == BOOK[None], 1 - error[:, None], error[:, None]).prod(axis=-1)
    left, right = INVENTORIES.T
    return np.asarray(prior)[:, None] * scores[left[:, None], left[None, :]] * scores[right[:, None], right[None, :]]


def analyze(table, prior, false_accept, false_reject):
    worlds = independent_readers(prior, false_accept, false_reject)
    assert np.isclose(worlds.sum(), 1)
    actual1, actual2 = (INVENTORIES[:, i, None] for i in (0, 1))
    left, right = INVENTORIES.T
    # The attestation gate verifies actual capability, while agents only see
    # the model's noisy inventory estimate.
    a, b = table[0, left, 0], table[1, right, 0]
    cost = float(np.sum(worlds * SIGNAL_COST * (a + b)))
    valid, invalid = 0., 0.
    for keep in MASKS:
        x = table[0, left, 1 + 2 * a + b * keep[0]][None, :]
        y = table[1, right, 1 + 2 * b + a * keep[1]][None, :]
        x_ok, y_ok = (x & actual1) == x, (y & actual2) == y
        mass = worlds * mask_weight(keep, LOSS)
        valid += float(np.sum(mass * (RECEIPT[x, y] == 3) * x_ok * y_ok))
        invalid += float(np.sum(mass * (~x_ok | ~y_ok)))
        cost += float(np.sum(mass * MESSAGE_COST * (ATTEMPT[x].astype(int) + ATTEMPT[y])))
    trained = 35 + ACHIEVABLE * valid - cost

    # Enumerate the same 144 no-signal maps against the same faulty reader.
    x, y = ACTIONS[:, None, left, None], ACTIONS[None, :, right, None]
    l, r = actual1.T[None, :, None], actual2.T[None, :, None]
    supported = ((x & l) == x) & ((y & r) == y) & (RECEIPT[x, y] == 3)
    returns = ACHIEVABLE * supported - MESSAGE_COST * (ATTEMPT[x].astype(int) + ATTEMPT[y])
    silent = 35 + float(np.sum(returns * worlds.T, axis=(2, 3)).max())
    return {"trained": trained, "reader_matched_silent": silent, "gain": trained - silent,
            "unsupported_attempt_probability": invalid, "full_receipt_probability": valid * (1 - LOSS) ** 2}


def run():
    path = EVIDENCE / "buffered-fit.json"
    prior = json.loads((EVIDENCE / "dprk-routes.json").read_text())["arms"]
    archive = json.loads(path.read_text())
    table = np.asarray(archive["trained_tables"]["matched"])
    rows = {}
    for name, policies in prior.items():
        distribution = [w["probability"] for w in policies["silent"]["worlds"]]
        cases = [{"false_accept": fp, "false_reject": fn, **analyze(table, distribution, fp, fn)}
                 for fp in GRID for fn in GRID]
        assert np.isclose(cases[0]["trained"], archive["priors"][name]["both_10"]["matched_fit"]["net"])
        assert np.isclose(cases[0]["reader_matched_silent"],
                          archive["priors"][name]["both_10"]["exact_buffered_silent"]["net"])
        rows[name] = cases
    return {"scope": "Synthetic independent completeness-reading errors and 10% independent transport loss. "
                     "No errors swap one role for the other. The same reader and attestation apply to each arm.",
            "link_loss": LOSS, "priors": rows}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
