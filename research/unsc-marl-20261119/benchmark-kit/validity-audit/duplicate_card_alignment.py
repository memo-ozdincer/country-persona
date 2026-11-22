"""Audit which routing policies maximize the actual frozen record endpoints."""
import argparse
import json
from pathlib import Path

import numpy as np

from duplicate_card_records import CARD_IDS, FIT
from duplicate_card_routes import TEST, exact

METRICS = ("verified_points", "guard_clear_points", "release_eligible_points", "full_national_criteria")


def packets_by_receipt(report):
    return {
        frozenset() if receipt == "public" else frozenset(receipt.split("-")): packet
        for packet in report["packet_scores"]
        for receipt in [packet["id"].split("/")[-2]]
    }


def value_matrix(packets, metric):
    def value(left, right):
        card_ids = frozenset({CARD_IDS[left], CARD_IDS[right]} - {None})
        record = packets[card_ids]
        if metric == "guard_clear_points":
            return record["floor"] if record["critical_guard"] == "clear" else 0
        if metric == "release_eligible_points":
            eligible = record["critical_guard"] == "clear" and record["under_limit"] and record["ended"]
            return record["floor"] if eligible else 0
        if metric == "full_national_criteria":
            return len({"P1", "P2"} & set(record["met_units"]))
        return record["floor"]

    return np.array([[value(left, right) for right in range(3)] for left in range(3)])


def analyze(report):
    packets = packets_by_receipt(report)
    fit = json.loads(FIT.read_text())
    result = {}
    for name, probabilities in TEST.items():
        result[name] = {}
        for metric in METRICS:
            matrix = value_matrix(packets, metric)
            ceilings = exact(probabilities, matrix, 0)
            quantities = {}
            for arm, data in fit["arms"][name].items():
                actual = sum(w["probability"] * matrix[tuple(w["actions"])] for w in data["worlds"])
                assert actual <= ceilings["optional"][0] + 1e-9
                quantities[arm] = float(actual)
            result[name][metric] = {
                "frozen_policy": quantities,
                "ceiling_by_channel_if_optimized_for_this_metric": {k: v[0] for k, v in ceilings.items()},
            }
    return result


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("scores", nargs="+", type=Path)
    args = cli.parse_args()
    result = {path.parent.name: analyze(json.loads(path.read_text())) for path in args.scores}
    print(json.dumps(result, ensure_ascii=False, indent=2))
