"""Measure how much a fixed requester can gain across unobserved channel types."""
import argparse
import json

import numpy as np

import facilitator_baseline_request_fit as study

fit, R, D = study.fit, study.R, study.D


def audit(robust, public, target, prior, archive):
    opener, opening, reply, _ = study.problem(public, prior, robust)
    channels = tuple(fit.STRESS.values())
    gains = np.stack([x - x[:, :1] for x in
                      (study.returns(reply, opening, fit.value(target, channel)) for channel in channels)])
    by_state = np.where(D.CHAIR_LEGAL, gains.min(0), -np.inf)
    safe_local = by_state.argmax(-1)
    rows = np.arange(len(safe_local))
    values = gains[:, rows, fit.MAPS].sum(-1)
    feasible = (values >= -1e-10).all(0)
    assert feasible[0] and np.array_equal(fit.MAPS[0], [0] * len(rows))
    safe_episode = fit.MAPS[np.where(feasible, values.mean(0), -np.inf).argmax()]
    maximizer = fit.MAPS[values.mean(0).argmax()]
    policies = {"statewise_safe": safe_local, "episode_safe": safe_episode, "largest_mean": maximizer}
    optima = values.max(1)
    assert np.allclose(optima, [v["exact_same_responder"]["gain_over_no_request"] for v in archive.values()])
    numbers = {}
    for name, policy in policies.items():
        predicted = gains[:, rows, policy].sum(1)
        measured = [fit.measure((policy, reply), opener, opening, prior, target, h)["net"] -
                    row["no_request"]["net"] for h, row in zip(channels, archive.values(), strict=True)]
        assert np.allclose(predicted, measured, rtol=0., atol=1e-10)
        numbers[name] = {"request": policy.tolist(), "advantages": predicted.tolist(),
                         "mean": float(predicted.mean()), "minimum": float(predicted.min())}
    assert numbers["episode_safe"]["minimum"] >= -1e-10
    assert numbers["statewise_safe"]["minimum"] >= -1e-10
    return {"policies": numbers, "admissible_count": int(feasible.sum()), "all_request_maps": len(fit.MAPS),
            "separate_observed_channel_best": optima.tolist(),
            "value_of_observing_channel": float(optima.mean() - numbers["largest_mean"]["mean"])}


def run():
    expected = json.loads((study.EVIDENCE / "results.json").read_text())
    robust = json.loads(study.WEIGHTS.read_text())["robust"]
    held = study.archive.banks()
    public = held["resolution_2699"][0]
    held["resolution_2699"] = public, np.asarray(json.loads(
        (study.accounts.EVIDENCE / "apostrophe.json").read_text())["released_bank"])
    held["resolution_2699_rewrite"] = public, np.asarray(json.loads(
        (study.accounts.fixed.EVIDENCE / "results.json").read_text())["released_bank"])
    return {"channels": list(fit.STRESS), "conditions": {
        fam: {lab: audit(robust, public, target, R.TEST_PRIORS[lab], expected["evaluation"][fam][lab])
              for lab in fit.live.PRIORS}
        for fam, (public, target) in held.items()}}


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(run(), indent=2))
