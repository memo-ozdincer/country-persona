"""Check whether the regression's largest losses arise in the responder or question map."""
import json
import numpy as np

import facilitator_silence_joint_fit as study


def run():
    archive = study.budget.read(study.EVIDENCE / "responder-regression.json")
    scores = study.budget.read(study.OLD)["cases"]["2719"]["outcomes"]["70"]
    target = np.asarray(scores["terminal_scores"])
    channel = study.joint.held()["2719"][1]
    rows = archive["cases"]["2719"]["70"]
    result = {}
    for label, systems in rows.items():
        prior = study.R.TEST_PRIORS[label]
        original, alternative = ([
            np.asarray(systems[key]["policy"][role]) for role in ("left", "right", "request", "response")
        ] for key in ("response_aware", "regression"))
        assert all(np.array_equal(a, b) for a, b in zip(original[:2], alternative[:2], strict=True))
        paths = {"response_aware": original, "regression": alternative,
                 "regression_responder_only": (*original[:3], alternative[3]),
                 "regression_question_only": (*original[:2], alternative[2], original[3]),
                 "silence_with_aware_responder": (*original[:2], np.zeros(8, dtype=int), original[3]),
                 "silence_with_regressed_responder": (*original[:2], np.zeros(8, dtype=int), alternative[3])}
        base = systems["hindsight_no_request"]["net"]
        result[label] = {}
        for key, action in paths.items():
            outcome = study.joint.metric(action, prior, target, channel)
            result[label][key] = {"net_over_hindsight_no_request": outcome["net"] - base,
                                  "request_rate": outcome["expected_requests"]}
        for name in ("response_aware", "regression"):
            assert abs(result[label][name]["net_over_hindsight_no_request"]
                       - systems[name]["net_over_hindsight_no_request"]) < 1e-10
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
