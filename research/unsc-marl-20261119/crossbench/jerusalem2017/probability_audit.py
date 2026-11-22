"""Isolate finite-sample errors in the receiver's two fitted probability factors."""
import json
from pathlib import Path

import numpy as np

import estimate_receiver as estimation
import reward_receiver as reward
import transfer
import train_calibrator as earlier

HERE = transfer.HERE


def run():
    calibration = transfer.Calibration()
    fit_path = HERE / "estimated-receiver.json"
    fit = json.loads(fit_path.read_text())
    focus_prior = calibration.design_prior.T.copy()
    focus_prior /= focus_prior.sum(axis=1, keepdims=True)
    loss = calibration.question_loss
    seen_request = (1 - loss) * np.array([loss / (1 + loss), 1])
    emission = np.column_stack((1 - seen_request, seen_request))
    combinations = {
        "both_estimated": (fit["background"], fit["emission"]),
        "known_inventory_only": (focus_prior, fit["emission"]),
        "known_channel_only": (fit["background"], emission),
        "both_known": (focus_prior, emission),
    }
    _, branches, _ = earlier.data(calibration)
    cases = {}
    for name, values in reward.TEST.items():
        exact = reward.exact(calibration, values)
        control = earlier.evaluate(exact, calibration, branches)
        by_method = {}
        for method, (background, signal) in combinations.items():
            table = estimation.table(np.asarray(background), np.asarray(signal), values)
            outcomes = earlier.evaluate(table, calibration, branches)
            heldout = [key for key in outcomes if key.count("1") % 2]
            gaps = np.array([outcomes[key][prior] - control[key][prior]
                             for key in heldout for prior in calibration.priors])
            by_method[method] = {"decision_agreements": int((table == exact).sum()),
                                 "minimum_net_gap": float(gaps.min()), "maximum_net_gap": float(gaps.max())}
        assert by_method["both_known"]["decision_agreements"] == exact.size
        cases[name] = by_method
    return {"scope": "Replace one component at a time from the same sampled comparator with its known simulator value. "
                     "This is a mechanism check. The deployment comparisons never know the evaluation prior.",
            "code_sha256": transfer.routing.digest(Path(__file__)), "fit_sha256": transfer.routing.digest(fit_path),
            "case_metrics": cases,
            "exact_background": focus_prior.tolist(), "exact_emission": emission.tolist()}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
