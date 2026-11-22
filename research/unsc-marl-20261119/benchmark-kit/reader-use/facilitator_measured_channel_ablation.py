"""Separate the content of paid requests from the policy switches they induce."""
import argparse
import json

import numpy as np

import facilitator_measured_channel_fit as study

fit = study.fit


def run(evaluation):
    points = np.asarray(evaluation["authored_points"])
    actual = np.asarray(evaluation["held_admission"])
    result = {}
    for label, cases in evaluation["policies"].items():
        prior = fit.ROUTE.TEST_PRIORS[label]
        opener, opening = fit.context(points, prior)
        q, r = map(np.asarray, cases["ideal_fit"]["policy"])
        mq, mr = map(np.asarray, cases["measured_fit"]["policy"])
        quiet = np.zeros_like(q)
        policies = {
            "trained_pair": (q, r), "erased_policy_input": (q, r),
            "erased_writer_input": (q, r), "erased_everywhere": (q, r),
            "measured_reply": (q, mr), "measured_request": (mq, r),
            "same_responder_no_request": (quiet, r),
        }
        rows = {}
        for key, tail in policies.items():
            erase_writer = key in ("erased_writer_input", "erased_everywhere")
            erase_policy = key in ("erased_policy_input", "erased_everywhere")
            channel = np.broadcast_to(actual[0], actual.shape) if erase_writer else actual
            row = fit.measure(tail, opener, opening, prior, points, channel, erase=erase_policy)
            row["expected_requests"] = float(opening.sum((0, 1)) @ (tail[0] != 0))
            assert row["net"] <= cases["exact_held_joint"]["net"] + 1e-10
            rows[key] = row
        assert abs(rows["trained_pair"]["net"] - cases["ideal_fit"]["net"]) < 1e-10
        paid_fee = float(opening.sum((0, 1)) @ fit.D.QUERY_COST[q])
        assert abs(rows["erased_everywhere"]["net"] + paid_fee - rows["same_responder_no_request"]["net"]) < 1e-10
        result[label] = {"request_topic_by_opening": q.tolist(), "comparisons": rows}
    return result


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(run(study.read(study.EVIDENCE / "evaluation.json")), indent=2))
