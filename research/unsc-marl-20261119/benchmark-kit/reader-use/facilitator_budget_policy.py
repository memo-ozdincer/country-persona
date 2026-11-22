"""Fit receipt-aware policies to terminal rewards with a fixed word budget."""
import json
from hashlib import sha256
from itertools import product
from pathlib import Path
import sys

import numpy as np

import facilitator_passage_adaptive_fit as adaptive

joint, fit, D, R = adaptive.joint, adaptive.fit, adaptive.D, adaptive.R
HERE = joint.HERE
EVIDENCE = HERE / "facilitator-budget-policy-evidence"
VERBATIM = HERE / "live-2719-routing-transfer/verbatim-bound"
sys.path.insert(0, str(VERBATIM))
import replay_verbatim as verbatim

LIMITS = (70, 90, 110)


def read(path):
    return json.loads(path.read_text())


def projection(points, lengths, limit):
    words = {mask: sum(n for i, n in enumerate(lengths) if mask & (1 << i)) for mask in range(8)}
    return np.asarray([max(points[s] for s in range(8) if s & mask == s and words[s] <= limit)
                       for mask in range(8)])


def generic_lengths(path, prefix, labels):
    rows, = read(path).values()
    return tuple(len(rows[f"{prefix}/{slot}"].split()) + len(label.split())
                 for slot, label in enumerate(labels, 1))


def development():
    paths = [row[0].parent / "final-records.json" for row in joint.historic.SOURCES.values()]
    lengths = [generic_lengths(path, "reply/0", ("Source one", "Source two", "Source three")) for path in paths]
    banks = fit.OLD.base.cases()[0]
    sets, profiles = {"budget_fit": {}, "unbounded_fit": {}}, {}
    for index, (case, (public, target)) in enumerate(banks.items()):
        profile = tuple(int(n) for n in np.roll(lengths[index % len(lengths)], index % 3))
        profiles[case] = profile
        for limit in LIMITS:
            key = f"{case} / {limit}"
            for name in sets:
                cap = limit if name == "budget_fit" else sum(profile)
                sets[name][key] = tuple(projection(p, profile, cap) for p in (public, target))
    return sets, profiles, paths


def reviewed_prefix_bank(limit):
    datasets, _ = verbatim.inputs()
    notes = datasets["change_wording/declared"]
    by_slot = {n["desk"]: n for n in notes}
    ordered = [by_slot[c["speaker"]] for c in read(verbatim.live.PACKET)["cards"]]
    weights = {c["id"]: c["points"] for c in read(verbatim.live.PACKET)["criteria"]}
    labels = read(VERBATIM / "annotations.json")
    rules = read(VERBATIM / "grammar.json")["criteria"]
    rows = []
    for receive in range(8):
        got = [n for i, n in enumerate(ordered) if receive & (1 << i)]
        lengths = [range(len(verbatim.SPLIT.split(n["text"])) + 1) for n in got]
        candidates = [verbatim.evaluate(got, prefix, labels, rules, weights) for prefix in product(*lengths)]
        rows.append(42 + max(c["guarded_points"] for c in candidates if c["words"] <= limit))
    previous = read(VERBATIM / "results.json")
    if str(limit) in previous["cases"]["change_wording/declared"]["budget"]:
        expected = previous["cases"]["change_wording/declared"]["budget"][str(limit)]["reviewed_optimum"]["points"]
        assert rows[7] == 42 + expected
    return np.asarray(rows)


def evaluate(public, unbounded_public, target, prior, channel, models):
    direct_start = joint.exact_no_request(prior, public, fit.PERFECT)
    declared, _ = joint.block(direct_start, prior, public, fit.PERFECT)
    quiet = joint.exact_no_request(prior, target, channel)
    oracle, _ = joint.block(quiet, prior, target, channel)
    teams = {"declared_block": declared, "hindsight_no_request": quiet, "hindsight_block": oracle}
    for name, model in models.items():
        greedy, _ = adaptive.contextual_policies(public, prior, model)
        teams[name] = greedy
    old, _ = adaptive.contextual_policies(unbounded_public, prior, models["archived_budget_input"])
    teams["archived_unbounded_input"] = old
    teams["budget_openers_unbounded_tail"] = (*teams["budget_fit"][:2], *teams["unbounded_fit"][2:])
    teams["unbounded_openers_budget_tail"] = (*teams["unbounded_fit"][:2], *teams["budget_fit"][2:])
    budget = teams["budget_fit"]
    teams["declared_tail_budget_openers"] = (
        *budget[:2], *fit.exact(public, joint.opening(*budget[:2], prior), fit.PERFECT)
    )
    result = {}
    quiet_net = joint.metric(quiet, prior, target, channel)["net"]
    for name, team in teams.items():
        score = joint.metric(team, prior, target, channel)
        result[name] = {"net": score["net"], "vs_hindsight_no_request": score["net"] - quiet_net,
                        "requests": score["expected_requests"], "guarded_points": score["guarded_points"],
                        "first_actions": [np.asarray(d).tolist() for d in team[:3]]}
    return result


def run():
    sets, profiles, paths = development()
    models = {name: adaptive.train(rows) for name, rows in sets.items()}
    archive = adaptive.EVIDENCE / "results.json"
    models["archived_budget_input"] = read(archive)["fit"]
    held = joint.held()
    assert not {tuple(points) for points, _ in held.values()} & {
        tuple(public) for public, _ in fit.OLD.base.cases()[0].values()
    }
    scripts = {"2719": verbatim.live.REPLIES, "2504": HERE / "facilitator-2504-routing-evidence/final-records.json"}
    labels = {"2719": ("Procedural officer", "United States", "France"),
              "2504": ("Procedural officer", "Belgium", "Russian Federation")}
    cases = {}
    for case, (full, channel) in held.items():
        lengths = generic_lengths(scripts[case], "0", labels[case])
        outcome = {}
        for limit in LIMITS:
            public = projection(full, lengths, limit)
            actual = reviewed_prefix_bank(limit) if case == "2719" else public
            assert all(actual[i] <= actual[j] for i in range(8) for j in range(8) if i & j == i)
            outcome[str(limit)] = {
                "public_scores": public.tolist(), "terminal_scores": actual.tolist(),
                "priors": {label: evaluate(public, full, actual, R.TEST_PRIORS[label], channel, models)
                           for label in fit.live.PRIORS}}
        cases[case] = {"generic_note_words_with_labels": lengths, "outcomes": outcome}
    sources = (Path(__file__).resolve(), EVIDENCE / "protocol.md", archive,
               VERBATIM / "annotations.json", VERBATIM / "grammar.json", *paths, *scripts.values())
    return {"training_profiles": profiles,
            "updates_per_new_fit": joint.UPDATES,
            "training": {k: v for k, v in models.items() if k != "archived_budget_input"},
            "cases": cases,
            "sha256": {str(p.relative_to(HERE)): sha256(p.read_bytes()).hexdigest() for p in sources}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
