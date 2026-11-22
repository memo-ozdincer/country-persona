"""Replay frozen routing with a two-clause reader and a reader-matched silent control."""
import argparse
from collections import Counter
import json
from pathlib import Path

import numpy as np

from duplicate_card_atomic import CLAUSES, EVIDENCE, entries, hashes, observations
from duplicate_card_semantic_review import (
    FAULTS, STRESSES, best_silent_through_reader, digest, read_all, reward_tables, simulate,
)

READERS = ("pooled", "all_orders_agree", "clause_first", "clause_agreement", "oracle")


def read_probes(directory, prompts, expected_hashes):
    action_path = directory / "actions.jsonl"
    complete = json.loads((directory / "complete.json").read_text())
    launch = json.loads((directory / "launch.json").read_text())
    original = json.loads((EVIDENCE / "semantic/launch.json").read_text())
    assert launch["model_path"] == original["model_path"]
    assert launch["sha256"] == expected_hashes
    assert complete["sha256"] == digest(action_path)
    raw = list(map(json.loads, action_path.read_text().splitlines()))
    rows = {tuple(row["observation"]): row for row in raw}
    prompts = list(prompts)
    assert len(rows) == len(raw) == complete["records"] == len(prompts)
    for prompt in prompts:
        row = rows[prompt["observation"]]
        assert row["messages"] == prompt["messages"] and row["legal"] == list(prompt["legal"])
        assert len(row["scores"]) == len(row["legal"]) and np.isfinite(row["scores"]).all()
    return rows, complete["sha256"]


def decide(rows, source, variant):
    votes = {}
    margins = {}
    for clause in CLAUSES:
        votes[clause], margins[clause] = [], []
        for order in range(2):
            row = rows[source, variant, clause, order]
            scores = dict(zip(row["legal"], row["scores"], strict=True))
            margin = scores[1] - scores[0]
            votes[clause].append(int(margin > 0))
            margins[clause].append(margin)
    first = [clause for clause, decisions in votes.items() if decisions[0]]
    # Require both orders to support one clause and both to reject its rival.
    agreed = [clause for clause in CLAUSES if votes[clause] == [1, 1]
              and all(votes[other] == [0, 0] for other in CLAUSES if other != clause)]
    return {"votes": votes, "yes_minus_no_logits": margins,
            "clause_first": first[0] if len(first) == 1 else 0,
            "clause_agreement": agreed[0] if len(agreed) == 1 else 0}


def report(directory):
    raw, checksum = read_probes(directory, observations(), hashes())
    bundle, bundle_raw = read_all(EVIDENCE / "semantic")
    readings = {}
    counts = {name: Counter(correct=0, unsupported=0, missed_complete=0, false_rejection=0)
              for name in READERS}
    for case, source, variant, _, truth in entries():
        key = (case, source, variant)
        row = {**bundle[key], **decide(raw, source, variant), "oracle": truth}
        assert row["truth"] == truth
        readings[key] = row
        for name in READERS:
            found = row[name]
            counts[name].update(correct=int(found == truth),
                                unsupported=int(found != 0 and found != truth),
                                missed_complete=int(truth != 0 and found != truth),
                                false_rejection=int(truth != 0 and found == 0))

    return {
        "scope": "Exposed DPRK fixture. Both critical clauses checked on every passage without role metadata. "
                 "Other required facts are held fixed within each source family. "
                 "Exact replay uses the original routed records, no new writer output.",
        "actions_sha256": checksum,
        "measured_probe_budget": {
            "full_requirement": probe_budget(row for key, row in bundle_raw.items() if key[0] == "dprk"),
            "two_clause": probe_budget(raw.values()),
        },
        "probes_per_passage": dict(pooled=3, all_orders_agree=3, clause_first=2, clause_agreement=4),
        "passage_accuracy": counts,
        "passage_readings": [{"key": key, **row} for key, row in readings.items()],
        "evaluations": replay(readings, READERS),
    }


def replay(readings, readers):
    archive = json.loads((EVIDENCE / "buffered-fit.json").read_text())
    table = np.asarray(archive["trained_tables"]["matched"])
    routes = json.loads((EVIDENCE / "dprk-routes.json").read_text())
    reward = reward_tables()["dprk"]
    evaluations = []
    for prior_name, values in routes["arms"].items():
        prior = [world["probability"] for world in values["silent"]["worlds"]]
        for loss, rates in FAULTS.items():
            for style_name, style in STRESSES.items():
                for reader in readers:
                    base, silent = best_silent_through_reader(
                        "dprk", prior, reward[1, 2] - reward[0, 0], rates[1], style, reader, readings,
                    )
                    quiet = simulate("dprk", prior, reward, silent, rates, style, reader, readings)
                    fit = simulate("dprk", prior, reward, table, rates, style, reader, readings)
                    assert np.isclose(quiet["net"], base + reward[0, 0])
                    evaluations.append({"prior": prior_name, "loss": loss, "style": style_name,
                                        "reader": reader, "fit": fit, "optimized_silence": quiet,
                                        "net_gain": fit["net"] - quiet["net"]})
    return evaluations


def probe_budget(rows):
    rows = list(rows)
    return {"probes": len(rows), "input_tokens": sum(len(row["input_ids"]) for row in rows),
            "mean_answer_letter_mass": float(np.mean([row["legal_mass"] for row in rows]))}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(report(args.directory), indent=2))
