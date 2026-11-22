"""Replay the rubric that credits correct sequence without an explicit withdrawal motive."""
import argparse
from copy import deepcopy
import json

import numpy as np

import facilitator_2504_routing_replay as study
import facilitator_2504_routing_atoms as atoms


def run(admissions, weights):
    alternate = deepcopy(admissions)
    for name, row in alternate["replies"].items():
        q, c = map(int, name.split("/"))
        if c == 3:
            before, sep, _ = row["reply"].partition("Russia withdrew its separate draft S/2020/25.")
            assert sep
            phrase = next(text for text in ("Following the adoption of Resolution 2504, ",
                                            "After Resolution 2504 was adopted, ") if before.endswith(text))
            row["assessment"]["required"][2] = [phrase + sep]
            row["passed"] = bool(row["ended"] and row["words"] <= 52 and all(row["assessment"]["required"])
                                 and not row["assessment"]["errors"])
            alternate["matrix"][q][c] = int(row["passed"])
    alternate["passed_replies"] = sum(x["passed"] for x in alternate["replies"].values())
    whole = study.run(np.asarray(alternate["matrix"]), weights)
    return {"definition": "The held candidate must state the correct draft and withdrawal after the adoption. "
                          "It may omit Russia's motivation, which the original case's final rubric does not require.",
            "admission": alternate, "whole_replay": whole, "atom_replay": atoms.run(alternate, whole)}


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    replies = study.trained.read(study.study.EVIDENCE / "admission.json")
    weights = study.trained.read(study.study.archive.EVIDENCE / "fits.json")
    print(json.dumps(run(replies, weights), ensure_ascii=False, indent=2))
