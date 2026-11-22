"""Measure planner and fitted components in the same certificate replay."""
import json

import numpy as np

import facilitator_passage_joint_fit as study


def run():
    archive = study.historic.read(study.EVIDENCE / "results.json")
    result = {}
    for docket, (points, channel) in study.held().items():
        result[docket] = {}
        for label, case in archive["cases"][docket].items():
            shaped = {
                name: tuple(np.asarray(role) for role in case["policies"][name]["team"])
                for name in ("joint_fit", "declared_block_planner")
            }
            fitted, planner = shaped.values()
            prior = study.R.TEST_PRIORS[label]
            shared_baseline = case["policies"]["hindsight_no_request"]["net"]
            teams = {
                "fit": fitted,
                "planner_opening_only": (*planner[:2], *fitted[2:]),
                "planner_followup_only": (*fitted[:2], *planner[2:]),
                "planner": planner,
            }
            row = {}
            for name, team in teams.items():
                scores = study.metric(team, prior, points, channel)
                row[name] = {
                    "net": scores["net"],
                    "net_over_no_request": scores["net"] - shared_baseline,
                    "expected_requests": scores["expected_requests"],
                }
            assert abs(row["fit"]["net"] - case["policies"]["joint_fit"]["net"]) < 1e-10
            assert abs(row["planner"]["net"] - case["policies"]["declared_block_planner"]["net"]) < 1e-10
            result[docket][label] = row
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
