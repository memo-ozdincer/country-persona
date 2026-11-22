"""Fit a corrective reviewer with and without frozen source representations."""
import argparse
from importlib.util import module_from_spec, spec_from_file_location
from unittest.mock import patch
from collections import defaultdict
from pathlib import Path
from statistics import mean

import numpy as np

import collect as capture
import staged_route as existing

HERE, e, team, prior = capture.HERE, capture.e, capture.team, existing.prior
PC = 6
spec = spec_from_file_location('verified_balance_scorer', HERE.parent / 'score.py')
balance_score = module_from_spec(spec)
spec.loader.exec_module(balance_score)


def lock():
    files = (Path(__file__), HERE/"plan.json", HERE/"protocol.md", Path(existing.__file__),
             Path(prior.__file__), HERE.parent/"results.json", Path(balance_score.__file__))
    return {"dimensions":PC, "input_sha256":{str(p.relative_to(team.STUDY)):team.pin(p) for p in files}}


def rows():
    archive = defaultdict(dict)
    for row in capture.lab.old_rows():
        group, case, n = row["observation"]
        archive[group, case][n] = row
    calls = defaultdict(dict)
    for row in capture.lines("calls.jsonl"):
        group, case, n = row["observation"]
        assert n not in calls[group, case]
        calls[group, case][n] = row
    assert len(calls) == 27
    gold = team.read(HERE.parent/"results.json")["decisions"]
    result, changes = [], []
    for item in gold:
        case = item["case"]
        cohort = "routed" if item["cohort"] == "archive" else "held"
        scene = (cohort, case)
        data = calls[scene]
        assert set(data) == {0, 2, 3}
        for n, captured in data.items():
            if n == 0:
                expected = archive[scene][0]
                assert captured["messages"] == expected["messages"]
                if team.mapped(captured)[1] != team.mapped(expected)[1]:
                    changes.append(case)
        native = [data[0], archive[scene][1], data[2], data[3]]
        with patch.object(prior, 'score', balance_score):
            row = prior.encode(native, case, case.split("/")[0] if cohort=="routed" else "myanmar", item["truth"])
        result.append(row | {"projected":np.array([data[n]["features"] for n in (2,3)])})
    return result, changes


def rotate(train):
    matrix = np.concatenate([r["projected"] for r in train], axis=0)
    center = matrix.mean(axis=0)
    _, _, basis = np.linalg.svd(matrix-center, full_matrices=False)
    axes = basis[:PC].T
    # Fix each SVD sign before persisting the transform.
    signs = np.sign(axes[np.abs(axes).argmax(axis=0), np.arange(PC)])
    axes *= signs
    scale = ((matrix-center)@axes).std(axis=0).clip(min=.05)
    def view(row):
        extra = np.clip((row["projected"] - center) @ axes / scale, -3, 3)
        return row | {"z":np.column_stack((row["z"], extra))}
    return view, {"center":center.tolist(), "axes":axes.tolist(), "scale":scale.tolist()}


def fit(train, dimensions):
    mass = existing.family_weight(train)
    def reviewer(w):
        value = 0.
        gradient = np.zeros_like(w)
        for row, weight in zip(train, mass, strict=True):
            p = existing.receiver(row, w)
            returns = row["reply_rewards"]
            reward = (p * returns).sum(axis=1)
            value += weight * float(reward.mean())
            gradient += weight * row["z"].T @ (p * (returns-reward[:,None])) / 2
        return value, gradient - prior.L2*w
    receiver, review_trace = existing.update(np.zeros((dimensions,3)), reviewer)
    branches = []
    for row in train:
        picks = existing.receiver(row,receiver).argmax(axis=1)
        branches.append(np.r_[row["opening"], row["reply_rewards"][np.arange(2),picks]-prior.COST])

    def proposer(w):
        value, gradient = 0., np.zeros_like(w)
        for row, weight, returns in zip(train, mass, branches, strict=True):
            p = prior.softmax(row["x"]@w, [True,row["first"]!=2,True,True])
            choice = float(p@returns)
            value += weight*choice
            gradient += weight*np.outer(row["x"],p*(returns-choice))
        return value, gradient-prior.L2*w
    proposal, proposal_trace = existing.update(np.zeros((4,4)), proposer)
    return (proposal,receiver), {"reviewer":review_trace,"proposer":proposal_trace}


def action(row, weights):
    visible = {k:row[k] for k in ("x","z","first","legal")}
    p, q = prior.strategies(visible,weights)
    proposals = [prior.stats(row,a,int(q[a-2].argmax()) if a>=2 else 0) for a in range(4)]
    a = int(p.argmax())
    score, paid, label = proposals[a]
    return {"net":score,"checks":paid,"relation":team.LABELS[label],
            "sampled_proposal_net":float(p@[x[0] for x in proposals]),
            "frozen_review_ceiling":max(x[0] for x in proposals),
            "query_nets":[x[0] for x in proposals[2:]],
            "best_no_query":max(x[0] for x in proposals[:2])}


def trial(train,test):
    enrich, transform = rotate(train)
    ordinary, base_trace = fit(train, 6)
    # Check the control against the already verified staged implementation.
    reference, trace = existing.staged(train)
    assert all(np.array_equal(a,b) for a,b in zip(ordinary,reference,strict=True))
    assert base_trace == {"reviewer":trace["reviewer_both_views"], "proposer":trace["proposer_live_branches"]}
    augmented, more_trace = fit([enrich(row) for row in train], 6+PC)
    fixed = prior.select_fixed(train)
    records = []
    for row in test:
        base, more = action(row,ordinary), action(enrich(row),augmented)
        first, _ = (row["first"],0)
        label, paid = prior.routed(row,*fixed)
        peers = {"staged":base, "represented":more,
                 "only_reviewer":action(enrich(row),(ordinary[0],augmented[1])),
                 "only_proposer":action(row,(augmented[0],ordinary[1])),
                 "first_only":{"net":prior.payoff(first,row["gold"]), "checks":0,"relation":team.LABELS[first]},
                 "fixed_train":{"net":prior.payoff(label,row["gold"])-prior.COST*paid,
                                "checks":paid,"relation":team.LABELS[label]}}
        records.append({"id":row["key"],"truth":team.LABELS[row["gold"]],"policies":peers})
    summary = {arm:{k:mean(row["policies"][arm][k] for row in records) for k in values if k in
                     {"net","checks","sampled_proposal_net","frozen_review_ceiling"}}
               for arm,values in records[0]["policies"].items()}
    for arm, metrics in summary.items():
        metrics["correct"] = sum(r["policies"][arm]["relation"]==r["truth"] for r in records)
        metrics["wrong_decisive"] = sum(r["policies"][arm]["relation"] not in (r["truth"],"unknown") for r in records)
        if "frozen_review_ceiling" in metrics:
            metrics["useful_queries"] = sum(max(r["policies"][arm]["query_nets"]) >
                                             r["policies"][arm]["best_no_query"] for r in records)
    return {"training_families":sorted({r["family"] for r in train}),"fixed_rule":list(fixed),
            "transform":transform,"weights":{"staged":[w.tolist() for w in ordinary],
                                             "represented":[w.tolist() for w in augmented]},
            "objective":{"staged":base_trace,"represented":more_trace},
            "records":records,"summary":summary}


def run():
    assert lock() == team.read(HERE/"scoring-plan.json")
    verified = team.read(HERE/"verified.json")
    assert team.pin(capture.OUT/"calls.jsonl") == verified["evidence_sha256"]["calls.jsonl"]
    roster, changes = rows()
    fitting = [r for r in roster if r["family"]!="myanmar"]
    folds = {family:trial([r for r in fitting if r["family"]!=family],
                          [r for r in fitting if r["family"]==family])
             for family in sorted({r["family"] for r in fitting})}
    assert all(k not in v["training_families"] for k,v in folds.items())
    macro = {arm:{k:mean(v["summary"][arm][k] for v in folds.values()) for k in
                  ("net","checks")} for arm in next(iter(folds.values()))["summary"]}
    return {"archive_macro":macro,"archive_folds":folds,"identity_label_changes":changes,
            "myanmar":trial(fitting,[r for r in roster if r["family"]=="myanmar"]),
            "sha256":{p:team.pin(HERE/p) for p in ("scoring-plan.json","verified.json")}}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode",choices=("plan","run"))
    e.emit({"plan":lock,"run":run}[p.parse_args().mode]())
