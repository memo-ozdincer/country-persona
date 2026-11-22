"""Measure how reliable the desk hint must be for specialization to pay."""
import json

import roster_shift as shift

HERE = shift.HERE
relay = shift.relay


def crossover(baseline, right, wrong):
    if right <= wrong:
        return None
    return (baseline - wrong) / (right - wrong)


def ftf_calibration(fit):
    policy = {shift.transfer.immutable(row["local_state"]): row["probabilities"] for row in fit["policy"]}
    clean = fit["trained_record"]
    bank = shift.transfer.ftf_bank()
    wrong = []
    for target, anchor in relay.SCENARIOS:
        physical = shift.distribution(set(target) - {anchor}, fit["trained_strength"], 0)
        swapped = {(b, a): value for (a, b), value in physical.items()}
        dist = shift.transfer.outcomes(policy, target, anchor, swapped)
        wrong.append(shift.score(relay.KEYS, bank, target, anchor, physical, {"wrong": dist}))
    old = clean["old"]["net_gain_over_anchor"]
    correct = clean["new"]["net_gain_over_anchor"]
    wrong_value = shift.transfer.mean(wrong)["wrong"]["net_gain_over_anchor"]
    return {"old": old, "correct": correct, "wrong": wrong_value, "threshold": crossover(old, correct, wrong_value)}


def run():
    path = HERE / "specialist-fit-results.json"
    fitted = shift.transfer.read(path)
    calibrated = ftf_calibration(fitted)
    threshold = calibrated["threshold"]
    assert 0. <= threshold <= 1.
    cases = {}
    for family, priors in fitted["transfer"].items():
        correct = priors["strong_specialist_B"]["mean"]
        wrong = priors["mislabelled_specialist_B"]["mean"]
        key = "net_gain_over_anchor"
        best, invalid = correct["trained_joint"][key], wrong["trained_joint"][key]
        fallback = correct["frozen_aligned"][key]
        fixed = correct["known_prior_fixed"][key]
        assert abs(fallback - wrong["frozen_aligned"][key]) < 1e-9
        assert abs(fixed - wrong["known_prior_fixed"][key]) < 1e-9
        scenarios = []
        # Exact mixture of the two episodes with the same hidden-roster prior.
        # A declared reliability informs only the outer policy selection.
        for reliable in sorted({.5, .7, .8, .9, .95, 1., threshold}):
            choice = "specialized" if reliable >= threshold else "frozen"
            expected = reliable * best + (1 - reliable) * invalid
            chosen = expected if choice == "specialized" else fallback
            scenarios.append({"hint_reliable": reliable, "specialist_expected": expected,
                              "calibrated_choice": choice, "calibrated_expected": chosen,
                              "difference_from_frozen": chosen - fallback,
                              "difference_from_known_prior_fixed": chosen - fixed})
        cases[family] = {"always_frozen": fallback, "correct_hint": best, "wrong_hint": invalid,
                         "known_prior_fixed": fixed,
                         "break_even_against_frozen": crossover(fallback, best, invalid),
                         "break_even_against_known_prior_fixed": crossover(fixed, best, invalid),
                         "reliability_sensitivity": scenarios}
    return {"scope": "Assumed hint reliability with matching hidden-world distributions. The cutoff is derived only on the "
                     "fitted written-vote task and applied unchanged to the transfer dockets. These are expectations over "
                     "specified probabilities, not estimates of real archive accuracy.",
            "policy_artifact_sha256": shift.runner.digest(path), "calibration": calibrated, "families": cases}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
