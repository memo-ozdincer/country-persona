"""Grade the protected summaries on the four pivotal receipt views."""
import importlib.util
import json
from math import isclose
from unittest.mock import patch

import memo
import tally

HERE = tally.HERE
spec = importlib.util.spec_from_file_location("documentary_198_score", HERE.parent/"score.py")
score = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score)


def read(name):
    return memo.s.read(HERE/name)


def run():
    deck = read("deck.json")
    normal_read = score.read
    with patch.object(score, "read", lambda name: read(name) if name == "marks.json" else normal_read(name)):
        assessed = score.scores(deck)
    old = normal_read("scores.json")
    derived = normal_read("replay.json")
    locked = normal_read("plan.json")
    changes = {}
    for mode, pairs in locked["pairs"].items():
        selection = []
        for row in pairs:
            left, right = (row[key] for key in ("fixed", "fitted"))
            if old[f"{left}/literal"]["settled"] == old[f"{right}/literal"]["settled"]:
                continue
            assert left in assessed and right in assessed
            selection.append(row)
        separate = {}
        for arm in ("literal", "scoped", "tally"):
            bank = assessed if arm == "tally" else {k.split("/")[0]: v for k,v in old.items() if k.endswith("/"+arm)}
            separate[arm] = {key: sum(p["mass"]*(bank[p["fitted"]][key]-bank[p["fixed"]][key]) for p in selection)
                             for key in ("settled_release", "released")}
        assert isclose(separate["literal"]["settled_release"],
                       derived["conditional"][mode]["literal"]["paired_rank_minus_fixed"]["settled_release"],abs_tol=1e-9)
        changes[mode] = dict(paired_changes=separate, absolute_pivotal_mass=sum(p["mass"] for p in selection))
    switch = derived["switch_by_regime"]
    mean_change = {arm: sum(changes[mode]["paired_changes"][arm]["settled_release"]*switch[mode]
                                   for mode in changes)/len(changes) for arm in ("literal", "scoped", "tally")}
    return dict(assessments=assessed, changed_trajectories=changes, adaptive_mean_pivotal_settlement_gain=mean_change)


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
