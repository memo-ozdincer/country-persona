"""Use paired simulated calibration trials to choose communication or silence."""
from hashlib import sha256
from itertools import product
from math import log, sqrt
import json

import numpy as np

from duplicate_card_noisy_reader_fit import (
    EVIDENCE, LEFT, MASKS, POLICY, RECEIPT, RESPONSES, RIGHT, ANNOUNCEMENTS,
    compile_table, evaluate, evaluation_cases, mask_weight, values, weighted_payoff,
)

CALIBRATION = EVIDENCE / "noisy-reader-fit.json"
TICK = .05
GAIN_TICKS = 280
RISK_FAMILY = .05
PILOT_COUNTS = (4096, 262144)
SEED = 185601
MAX_TICKS = 290


def response(table, seen):
    a, b = table[0, LEFT, 0], table[1, RIGHT, 0]
    x = table[0, LEFT, 1 + 2 * a + b * seen[0]]
    y = table[1, RIGHT, 1 + 2 * b + a * seen[1]]
    bill = a + b + 4 * ((x != 0).astype(int) + (y != 0))
    return x, y, bill


def reward_ticks(action, delivered):
    left, right, cost = action
    left = (left & LEFT[:, None] == left) * left * delivered[0]
    right = (right & RIGHT[:, None] == right) * right * delivered[1]
    return GAIN_TICKS * (RECEIPT[left, right] == 3) - cost


def paired_law(challenger, silent, world, loss):
    mass = np.zeros(2 * MAX_TICKS + 1)
    for seen, delivered in product(MASKS, repeat=2):
        weight = mask_weight(seen, loss) * mask_weight(delivered, loss)
        delta = reward_ticks(response(challenger, seen), delivered) - reward_ticks(response(silent, seen), delivered)
        assert np.max(np.abs(delta)) <= MAX_TICKS
        mass += weight * np.bincount((delta + MAX_TICKS).ravel(), weights=world.ravel(), minlength=len(mass))
    assert np.isclose(mass.sum(), 1)
    possible = np.flatnonzero(mass)
    return (possible - MAX_TICKS) * TICK, mass[possible] / mass.sum()


def run():
    cases = list(evaluation_cases())
    frozen = np.asarray(json.loads(POLICY.read_text())["trained_tables"]["matched"])
    known = json.loads(CALIBRATION.read_text())["evaluation"]
    per_case = RISK_FAMILY / (len(cases) * len(PILOT_COUNTS))
    rows = []
    for index, (prior, regime, link, world, loss) in enumerate(cases):
        rng = np.random.default_rng(SEED + index)
        observed, payout = weighted_payoff(world, 14., loss)
        zero = (ANNOUNCEMENTS[0],) * 2
        table = values(observed, payout, loss, zero)
        chosen = np.unravel_index(table.argmax(), (len(RESPONSES),) * 2)
        silent = compile_table(zero, chosen)
        support, mass = paired_law(frozen, silent, world, loss)
        expected = float(mass @ support)
        archived = known[prior][regime][link]["prior_frozen"]["gain_over_same_reader_silent"]
        assert np.isclose(expected, archived)
        width = float(support[-1] - support[0])
        # Share draws across repeated pilots while using a Bonferroni budget
        # across all conditions and both inspection sizes.
        counts = np.zeros(len(mass), dtype=int)
        pilots = {}
        last = 0
        for n in PILOT_COUNTS:
            counts += rng.multinomial(n - last, mass)
            estimate = float((counts @ support) / n)
            # Use a predeclared support width, independent of the pilot. The
            # asymmetric range from fees is at most 29 net points overall.
            lower = estimate - 29 * sqrt(log(1 / per_case) / (2 * n))
            admitted = lower > 0
            pilots[str(n)] = {"estimated_gain": estimate, "lower_bound": lower,
                               "communicate": admitted, "actual_selected_gain": expected if admitted else 0.}
            last = n
        assert width <= 29
        rows.append({"prior": prior, "reader_regime": regime, "link": link,
                     "true_challenger_gain": expected, "support_range": width, "pilots": pilots,
                     "unsupported_attempts_challenger": evaluate(frozen, world, loss, 14.)["unsupported_attempt_probability"]})
    return {"scope": "Synthetic paired calibration of an existing learned policy against a same-reader silent oracle. "
                     "Pilots are independent of the exact return used to audit decisions. "
                     "Each draw represents two potential rollouts with common inputs.",
            "pilot_sizes": PILOT_COUNTS, "family_risk": RISK_FAMILY, "per_inspection_risk": per_case,
            "first_seed": SEED, "archive_sha256": sha256(CALIBRATION.read_bytes()).hexdigest(), "cases": rows}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
