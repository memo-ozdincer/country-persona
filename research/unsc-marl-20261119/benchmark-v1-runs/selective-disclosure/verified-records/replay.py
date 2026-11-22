"""Replay every reachable receipt through the independent record verifier."""
from collections import defaultdict
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import re
from statistics import mean
import sys
from unittest.mock import patch

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "documentary-198"))
import history_prior as history
import joint_opener as opener
import memo
import ranking
import recipient
import render
import selective as s

MODES = ("balanced", "uniform")
POLICIES = ("fixed", "rank-fit", "switch-32")


def ledger(grid, view):
    return tuple((grid.packages[r[0]], r[1]) if r is not None else None for r in view)


def run_cases():
    torch.set_num_threads(1)
    registry = s.read(s.original.REGISTRY)
    entries = {r["draw"]: r for r in registry["accepted"]}
    original = torch.tensor(s.read(s.FIT)["weights"], dtype=torch.float64)
    rank_result = s.read(HERE.parent/"ranking.json")
    ranking_w = np.asarray(rank_result["coef"])
    opener_w = np.asarray(s.read(HERE.parent/"joint-opener.json")["weights"])
    value_w = np.asarray(s.read(HERE.parent/"recipient.json")["weights"])

    def grid_for(draw):
        with patch.dict(s.shared.FIXTURES, {"records": s.original.fixture(entries[draw])}):
            return s.shared.Grid("records")

    held = tuple(registry["partition"]["reserved"])
    grids = {f"space-{i}": ("space", grid_for(i)) for i in held}
    grids.update({group: (group, s.shared.Grid(group)) for group in ("mali","myanmar")})
    archived_history = s.read(HERE.parent/"history-prior.json")["cases"]
    audited_example = s.read(HERE.parent/"documentary-198/replay.json")["equal_mixture"]["literal"]

    cases = {}
    for case, (family, grid) in grids.items():
        def position(balanced):
            data = s.shared.Experiment(grid, balanced)
            for index, role in enumerate(data.roles):
                if role == 2:
                    data.mask[index, 1:] = False
            raw = data.probabilities(original).numpy()
            first = opener.choose(data, raw, opener.basis(data, data.prior, raw), opener_w, s.base.FEE, "joint-fitted")
            table = recipient.aggregate(data, first)
            arms = ranking.measure(data, first, table, ranking_w, value_w)
            return data, {key: arms[key] for key in ("fixed","rank-fit")}, table
        inputs = [position(balanced) for balanced in (True, False)]
        assert inputs[0][0].states == inputs[1][0].states
        assert all(np.array_equal(inputs[0][1][arm][0], inputs[1][1][arm][0]) for arm in ("fixed","rank-fit"))
        post, mass = history.likelihoods(history.mass_distribution([r[2] for r in inputs], True))[0][32]
        switch = mass[post > .5].sum(0)

        tables = [memo.receipt_rows(grid, data, actions) for data, actions, _ in inputs]
        views = sorted({one for table in tables for pair in table for one in pair}, key=str)
        ids = {view: f"receipt-{i+1:02d}" for i, view in enumerate(views)}
        bank = {}
        for view in views:
            receipts = ledger(grid, view)
            text = render.render(grid, family, receipts)
            checked = render.verify(grid, family, receipts, text)
            bank[ids[view]] = dict(receipts=receipts, text=text, verification=checked)
        pairs_out, evaluations = {}, {}
        for mode, p, (_, actions, _), table in zip(MODES, switch, inputs, tables, strict=True):
            fee = actions["fixed"][1]["peer_rate"]*s.base.FEE
            assert abs(fee-actions["rank-fit"][1]["peer_rate"]*s.base.FEE)<1e-12
            values = {}
            for index, name in enumerate(("fixed","rank-fit")):
                values[name] = {metric: sum(prob*bank[ids[views[index]]]["verification"][metric]
                                             for views, prob in table.items())
                                for metric in ("release_points", "settled_points")}
            values["switch-32"] = {metric: values["fixed"][metric]+p*(values["rank-fit"][metric]-values["fixed"][metric])
                                   for metric in ("release_points", "settled_points")}
            prior = archived_history[case]["history"]["own+messages"]["horizons"]["32"]["policies"]
            for arm, metrics in values.items():
                expected_net = metrics["settled_points"]/70-fee
                reference = {"fixed": "fixed", "rank-fit": "rank", "switch-32": "posterior-switch"}[arm]
                assert abs(expected_net-prior[reference][mode]) < 1e-9
                metrics["net"] = expected_net
            pairs_out[mode] = [{ "fixed": ids[a], "rank-fit": ids[b], "mass": float(prob) }
                               for (a,b),prob in table.items()]
            evaluations[mode] = dict(fee=fee, switch=float(p), metrics=values)
        mixture = {arm: {metric: mean(evaluations[m]["metrics"][arm][metric] for m in MODES)
                          for metric in ("release_points","settled_points","net")} for arm in POLICIES}
        if case == "space-198":
            for arm in POLICIES:
                assert abs(mixture[arm]["release_points"]-audited_example[arm]["released"]) < 1e-9
                assert abs(mixture[arm]["settled_points"]-audited_example[arm]["settled_release"]) < 1e-9
        cases[case] = dict(records=bank, regimes=evaluations, paired_trajectories=pairs_out,
                           equal_mixture=mixture, verifier_checks=robustness(grid,family))
    summaries = {}
    for label, keys in (("reserved", [k for k in cases if k.startswith("space-")]),
                        ("transfer", ["mali","myanmar"])):
        summaries[label] = {arm: {metric: mean(cases[k]["equal_mixture"][arm][metric] for k in keys)
                                  for metric in ("release_points","settled_points","net")} for arm in POLICIES}
    roots = (Path(__file__), HERE/"render.py", HERE/"protocol.md",
             HERE.parent/"ranking.json", HERE.parent/"history-prior.json",
             HERE.parent/"documentary-198/replay.json", s.original.REGISTRY,
             *(s.SPACE.parent / group / "historical-task.json" for group in render.SOURCES))
    return dict(cases=cases, macro=summaries, pins={str(p.relative_to(render.WORKSPACE)):sha256(p.read_bytes()).hexdigest()
                                                   for p in roots})


def robustness(grid, family):
    options = [[None, *((label, value) for j,label in enumerate(grid.packages)
                       for value in sorted({card[j] for card in deck}))] for deck in grid.cards]
    checked = defaultdict(int)

    def reject(thunk, key):
        try:
            thunk()
        except ValueError:
            checked[key] += 1
        else:
            raise AssertionError(key)

    for view in product(*options):
        text = render.render(grid, family, view)
        check = render.verify(grid, family, view, text)
        checked["legal_receipts"] += 1
        checked["tie_evidence"] += int(any(len(v)>1 for v in render.independent_outcomes(grid, view)[0]))
        heading, history, scope, body = text.split("\n\n")
        wrong_heading = "Workshop disposition: " + ("impasse" if check["disposition"] != "impasse" else "unresolved")
        reject(lambda: render.verify(grid, family, view, "\n\n".join((wrong_heading,history,scope,body))), "wrong_disposition")
        reject(lambda: render.verify(grid, family, view, "\n\n".join((heading,history[:-1],scope,body))), "altered_history")
        reject(lambda: render.verify(grid, family, view, text.replace("no official action", "official action", 1)), "authority")
        reject(lambda: render.verify(grid, family, view, text.replace(f'Compatible completions: {check["completions"]}.',
                                                                     "Compatible completions: 0.",1)), "count")
        reject(lambda: render.verify(grid, family, view, text.replace("First desk", "Second desk", 1)), "owner_swap")
        if check["disposition"] == "unresolved":
            reject(lambda: render.verify(grid, family, view, text.replace("No common disposition.",
                                                                         "Every set has the same result.",1)), "wrong_witness")
            wrong_histogram = re.sub(r"×([1-9][0-9]*)", lambda m: f"×{int(m[1])+1}", text, count=1)
            reject(lambda: render.verify(grid, family, view, wrong_histogram), "wrong_witness_count")
        elif check["disposition"] != "impasse":
            unique_claim = text.replace("is among the winners", "is the sole winner", 1)
            reject(lambda: render.verify(grid, family, view, unique_claim), "unverified_uniqueness")
    reject(lambda: render.render(grid, family, [("X",0),None]), "unknown_package")
    reject(lambda: render.render(grid, family, [(grid.packages[0], True),None]), "invalid_grade")
    reject(lambda: render.render(grid, family, [None]), "invalid_role_slots")
    return dict(checked)


if __name__ == "__main__":
    print(json.dumps(run_cases(), ensure_ascii=False, indent=2))
