"""Validate evidence-backed annotations and replay final-record scores by policy."""
import argparse
import json
from pathlib import Path

import numpy as np

import routing
import writer


def check(row, review, focus):
    output = row["output"]
    payload = json.loads(row["messages"][1]["content"])
    allowed = {key: payload[key] for key in ("public_record", "focal_slip", "archival_backup") if key in payload}
    assert review["reason"] and review["guard"] in {"clear", "failed", "uncertain"}
    awarded = review["met"]
    assert set(awarded) <= set("01234")
    for key, evidence in awarded.items():
        grade = int(key)
        expected_source = "focal_slip" if grade == 0 else "archival_backup"
        assert evidence["record"] and evidence["record"] in output
        assert evidence[expected_source] and evidence[expected_source] in allowed[expected_source]
        assert grade == 0 or len(focus["backup_criteria"]) >= grade
    for quote in review.get("issues", {}).values():
        assert quote and quote in output
    words = len(output.split())
    ended = row["ended"] and words <= 85
    points = 35 + 7 * len(awarded)
    return {"raw": points,
            "release": points if ended and review["guard"] == "clear" else 0,
            "release_with_uncertain": points if ended and review["guard"] != "failed" else 0,
            "words": words, "guard": review["guard"], "credited_criteria": list(awarded)}


def replay_scores(prior, policy, points):
    q_loss, r_loss, q_cost, r_cost = routing.config()
    request, reply = policy
    value = 0.0
    for focus, pair in np.ndindex(prior.shape):
        requested = request[focus]
        on_target = sum(chance * (reply[pair][observed] == focus)
                        for observed, chance in ((0, q_loss), (requested, 1 - q_loss)))
        delivered = (1 - r_loss) * on_target
        value += prior[focus, pair] * (points[focus, 0] + delivered * (points[focus, 1] - points[focus, 0])
                                       - q_cost * requested - r_cost)
    return float(value)


def run(directory, annotation_path):
    task = routing.load()
    rows = writer.verify(directory)
    labels = writer.read(annotation_path)
    assert labels["scope"] and set(labels["rows"]) == set(rows)
    focus_lookup = {entry["id"]: entry for entry in task["focuses"]}
    graded = {name: check(row, labels["rows"][name], focus_lookup[name.split("/")[0]]) for name, row in rows.items()}
    bit_scores = {measure: np.array([[graded[f"{entry['id']}/{receipt}"][measure] for receipt in ("slip", "matched")]
                                     for entry in task["focuses"]])
                  for measure in ("raw", "release", "release_with_uncertain")}
    policies = writer.read(routing.HERE / "routing-results.json")["results"]
    fitted = writer.read(routing.HERE / "routing-fit.json")
    train = policies[fitted["training_prior"]]["policies"]

    def actions(entries):
        return {key: (row["sender"], row["receiver"]) for key, row in entries.items()}

    comparisons = {}
    for name, prior in routing.priors():
        sender, responder = fitted["learned_policy"]
        erased = [(row[0], row[0]) for row in responder]
        candidates = {"learned": (sender, responder), "learned_erased": (sender, erased),
                      **{f"train_frozen_{key}": policy for key, policy in actions(train).items()},
                      **{f"prior_informed_routing_{key}": policy for key, policy in actions(policies[name]["policies"]).items()}}
        comparisons[name] = {metric: {key: replay_scores(prior, policy, points) for key, policy in candidates.items()}
                             for metric, points in bit_scores.items()}
        for key, value in candidates.items():
            planned = replay_scores(prior, value, np.tile([42, 70], (4, 1)))
            assert np.isclose(planned, routing.measure(prior, *map(np.asarray, value))["net"])
    return {"scope": labels["scope"], "trace_sha256": writer.digest(directory / "transcript.jsonl"),
            "annotations_sha256": writer.digest(annotation_path), "records": graded,
            "scores_by_focus_and_receipt": {key: p.tolist() for key, p in bit_scores.items()}, "comparisons": comparisons}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    cli.add_argument("annotations", type=Path)
    args = cli.parse_args()
    print(json.dumps(run(args.directory, args.annotations), indent=2, ensure_ascii=False))
