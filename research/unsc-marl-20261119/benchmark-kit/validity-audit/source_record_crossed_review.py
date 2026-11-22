"""Compare raw rubric credit and guard-passing credit under one-revision swaps."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

import source_record_review as review
from source_record_crossed import BASE, FAMILY, PEER_DRAFTS, SOLO_DRAFTS


def scores(directory, annotations):
    mixed = review.score(directory, annotations)
    original = json.loads((BASE / "compare.json").read_text())["cases"][FAMILY]
    values = {
        "both_independent": original[SOLO_DRAFTS]["compact"],
        "first_peer_only": mixed[f"{FAMILY}/peer_revision_1_only/chair"],
        "second_peer_only": mixed[f"{FAMILY}/peer_revision_2_only/chair"],
        "both_peer": original[PEER_DRAFTS]["compact"],
    }
    def checked(row):
        return row["critical_guard"] == "clear" and row["under_limit"]
    def differences(payoff):
        base, first, second, both = (payoff(values[label]) for label in values)
        return {
            "first_revision_with_second_independent": first - base,
            "second_revision_with_first_independent": second - base,
            "first_revision_with_second_peer": both - second,
            "second_revision_with_first_peer": both - first,
            "interaction": both - first - second + base,
        }
    return {
        "scope": annotations["scope"],
        "cells": {k: {**row, "usable": checked(row)} for k, row in values.items()},
        "raw_point_deltas": differences(lambda row: row["floor"]),
        "guard_and_word_cap_pass_deltas": differences(lambda row: int(checked(row))),
        "source_sha256": sha256((directory/"transcript.jsonl").read_bytes()).hexdigest(),
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    cli.add_argument("--annotations", type=Path, required=True)
    args = cli.parse_args()
    print(json.dumps(scores(args.directory, json.loads(args.annotations.read_text())), indent=2, ensure_ascii=False))
