"""Replay the same router with exact-span capacity readings and scoped decoys."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import sys

import numpy as np

from duplicate_card_qualifier_review import report as qualifier_report
from duplicate_card_semantic_review import (
    EVIDENCE, FAULTS, best_silent_through_reader, reward_tables, simulate,
)

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "judge"))
from dprk_capacity_spans import report as capacity_report
sys.path.pop(0)

STYLES = {
    "original_or_missing": (("source/full", "full"), ("source/missing", "missing")),
    "reordered_or_reversed": (("source/reordered", "reordered"), ("source/reversed", "reversed")),
    "reordered_or_other_speaker": (("source/reordered", "reordered"), ("scope/other-speaker", "other_actor")),
    "reordered_or_other_item": (("source/reordered", "reordered"), ("scope/other-item", "other_agenda")),
}


def readings(japan, china, variants, qualifier_key):
    rows = {}
    for level, (japanese_variant, chinese_variant) in zip(("positive", "negative"), variants, strict=True):
        capacity = japan[japanese_variant]
        qualifier = china[chinese_variant]
        # The remaining required parts are identical within this fixture.
        rows["dprk", 1, level] = {"truth": int(capacity["truth"] == 1),
                                 "span_model": int(capacity["agreed_role"] == 1),
                                 "span_matcher": int(capacity["span_heuristic_role"] == 1)}
        china_prediction = 2 * int(qualifier[qualifier_key] == 1)
        rows["dprk", 2, level] = {"truth": 2 * int(qualifier["reason_truth"] == 1),
                                 "span_model": china_prediction, "span_matcher": china_prediction}
    return rows


def report(directory):
    capacities = capacity_report(directory)
    qualifier = qualifier_report(EVIDENCE / "qualifier-dprk")
    japan = {row["case"]: row for row in capacities["rows"]}
    china = {row["key"][2]: row for row in qualifier["passage_readings"] + qualifier["synthetic_scope_controls"]
             if row["key"][1] == 2}
    priors = json.loads((EVIDENCE / "dprk-routes.json").read_text())["arms"]
    router_path = EVIDENCE / "buffered-fit.json"
    router = np.asarray(json.loads(router_path.read_text())["trained_tables"]["matched"])
    reward = reward_tables()["dprk"]
    gain = reward[1, 2] - reward[0, 0]
    evals = []
    for style, variants in STYLES.items():
        for qualifier_name in ("reason_agreement", "reason_majority_posthoc"):
            # Earlier artifacts report a posthoc majority on the archived
            # fields and decoys. Report it as sensitivity, separately.
            fixed = readings(japan, china, variants, qualifier_name)
            for prior_id, loss, reader in product(priors, FAULTS, ("oracle", "span_model", "span_matcher")):
                prior = [r["probability"] for r in priors[prior_id]["silent"]["worlds"]]
                rate = FAULTS[loss]
                views = ("positive", "negative")
                best, silent = best_silent_through_reader("dprk", prior, gain, rate[1], views, reader, fixed)
                baseline = simulate("dprk", prior, reward, silent, rate, views, reader, fixed)
                assert np.isclose(baseline["net"], reward[0, 0] + best)
                learned = simulate("dprk", prior, reward, router, rate, views, reader, fixed)
                evals.append({"style": style, "china_rule": qualifier_name, "reader": reader,
                              "prior": prior_id, "loss": loss, "learned": learned, "optimal_silence": baseline,
                              "paired_gain": learned["net"] - baseline["net"]})
    return {
        "scope": "Replay of the frozen two-desk protocol and archived final-record scores. "
                 "A ground-truth receipt gate rejects false roles but still charges attempts. "
                 "DPRK passages and joint private inventories are development fixtures.",
        "capacity_probe_sha256": capacities["actions_sha256"],
        "qualifier_probe_sha256": qualifier["actions_sha256"],
        "learned_router_sha256": sha256(router_path.read_bytes()).hexdigest(),
        "readers": capacities["rows"],
        "evaluations": evals,
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    print(json.dumps(report(cli.parse_args().directory), ensure_ascii=False, indent=2))
