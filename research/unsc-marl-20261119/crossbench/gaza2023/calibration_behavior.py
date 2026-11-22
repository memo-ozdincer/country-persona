"""Check what the learned calibrated responder uses at execution."""
import json
from pathlib import Path

import numpy as np

import routing
from calibrate_partner import Calibration, HERE, read
from train_calibrator import data, evaluate


def run():
    calibration = Calibration()
    path = HERE / "factored-calibration-results.json"
    fit = read(path.name)
    table = np.asarray(fit["greedy_receiver_table"])
    _, branches, _ = data(calibration)
    reference = []
    for probe in routing.REQUESTS:
        public_state = tuple(-1 if seen else 1 for seen in probe)
        reference.append(calibration.terminal(public_state, "flexible")[0])
    exact = np.asarray(reference)
    # Rebind each observed outcome to the next focus without changing count,
    # attempts, packet loss, test schedules or probe fees.
    rotated = np.roll(routing.REQUESTS, 1, axis=1)
    order = [int(np.flatnonzero(np.all(routing.REQUESTS == row, axis=1))[0]) for row in rotated]
    shifted = evaluate(table[order], calibration, branches)
    unaffected = evaluate(table, calibration, branches)
    assert all(np.isclose(fit["evaluations"][sender]["learned"][p], unaffected[sender][p])
               for sender in unaffected for p in calibration.priors)
    held = [name for name, row in fit["evaluations"].items() if row["split"] == "excluded"]
    shifts = {prior: {name: unaffected[name][prior] - shifted[name][prior] for name in held}
              for prior in calibration.priors}
    return {"scope": "Same heldout partner, delivered probe events, reply budgets and loss. Rotate only the binding "
                     "of topic to observed probe result. Also match each greedy action to exact decoding.",
            "code_sha256": routing.digest(Path(__file__)), "learned_sha256": routing.digest(path),
            "exact_action_agreements": int((table == exact).sum()), "action_table_size": exact.size,
            "excluded_schedule_per_prior_worst_exact_score_gap": {
                prior: min(fit["evaluations"][name]["learned"][prior]
                           - fit["evaluations"][name]["same_probe_exact_decoding"][prior] for name in held)
                for prior in calibration.priors},
            "excluded_matched_minus_rotated_probe_by_prior": {
                prior: {"mean": float(np.mean(list(rows.values()))), "by_schedule": rows}
                for prior, rows in shifts.items()}}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
