"""Test public probes phrased like the mission on the observed drift case."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import factored_partner as factored
import language_partner as partner
import relay_population as population

HERE = partner.HERE
ASSIGNMENTS = {
    "draft": "Recover the relevant wording in Egypt's draft on changes to Jerusalem's status and where diplomatic missions could be established.",
    "united_states": "Find what the American representative told the Council in defending her country's negative vote and discussing where its embassy would go.",
    "united_kingdom": "Recover what Matthew Rycroft said about Britain's vote for Egypt's text and where Britain would keep its embassy.",
    "sweden": "Find how Olof Skoog justified Sweden's support and what he said the vote meant for earlier Council decisions.",
}


def requests():
    task = partner.load()
    assert set(ASSIGNMENTS) == {focus["id"] for focus in task["focuses"]}
    for mode in ("direct", "factored"):
        for focus in task["focuses"]:
            key = focus["id"]
            wording = ASSIGNMENTS[key]
            if mode == "direct":
                payload = {"desk_rule": partner.PROTOCOLS["statement_desk"], "assignment": wording,
                           "permitted_question": task["question"]}
                guide = partner.GUIDE
            else:
                payload = {"assignment": wording}
                guide = factored.GUIDE
            yield partner.replay.request(f"{mode}/{key}", 24, guide, payload, [])


def episode(generate):
    from itertools import batched

    rows = {}
    for batch in batched(requests(), 4):
        rows.update(generate(list(batch)))
    return [{"family": partner.load()["id"], "final": rows}]


def locks():
    return {**partner.locks(), "phase_probe": partner.digest(Path(__file__)),
            "prior_actions": partner.digest(HERE / "language-evidence/actions.json"),
            "previous_factored_actions": partner.digest(HERE / "factored-evidence/actions.json"),
            "population_experiment": partner.digest(HERE / "relay-population-results.json")}


def run(directory):
    with patch.object(partner.runner, "episode", episode), patch.object(partner.runner, "locks", locks):
        partner.runner.run(Path(partner.read(partner.writer.MODEL)["model"]), directory)


def report(directory):
    with patch.object(partner.replay, "episode", episode), patch.object(partner.replay, "locks", locks):
        rows = partner.replay.verify(directory)
    task = partner.load()
    probes = {}
    for mode in ("direct", "factored"):
        vocabulary = {task["question"]: 1, "PASS": 0} if mode == "direct" else {"STATEMENT": 1, "DRAFT": 0}
        keys = [f"{mode}/{focus['id']}" for focus in task["focuses"]]
        assert all(rows[key]["ended"] and rows[key]["output"] in vocabulary for key in keys)
        probes[mode] = [vocabulary[rows[key]["output"]] for key in keys]

    previous = partner.read(HERE / "language-evidence/actions.json")["desks"]["statement_desk"]
    normalized = partner.read(HERE / "factored-evidence/actions.json")["desks"]["statement_desk"]
    calibration = population.transfer.Calibration()
    calibration.points[:, 1] = 70
    points = population.physical_bank()
    conditions = {
        "previous_public_probe": (previous["probe"], previous["mission"]),
        "fresh_direct_public_probe": (probes["direct"], previous["mission"]),
        "repeat_mission_format_reference": (previous["mission"], previous["mission"]),
        "fresh_factored_public_probe": (probes["factored"], normalized["mission"]),
    }
    output = {}
    for name, (probe, mission) in conditions.items():
        measurement = population.across_orders(np.asarray(probe), np.asarray(mission), points, calibration)
        values = [row["estimated_channel"] - row["exact_no_probe"]
                  for order in measurement["evaluations"].values() for row in order["8"].values()]
        output[name] = {
            "probe": probe, "mission": mission,
            "canonical_net": measurement["evaluations"]["0123"]["8"]["correlated_development"],
            "mean_calibrated_gain": float(np.mean(values)), "minimum_calibrated_gain": float(min(values)),
            "wins": int(np.count_nonzero(np.asarray(values) > 1e-9)), "conditions": len(values),
        }
    return {"scope": "Fresh public dummy probes use third paraphrases. Mission actions come from the already "
                     "measured original or factored sender. The repeated-format reference reuses earlier mission "
                     "actions as counterfactual probes and is labeled as such. All comparisons pay four probes.",
            "trace_sha256": partner.digest(directory / "transcript.jsonl"), "probes": probes, "comparisons": output}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "score"))
    cli.add_argument("directory", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        run(args.directory)
    else:
        print(json.dumps(report(args.directory), ensure_ascii=False, indent=2))
