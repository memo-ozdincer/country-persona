"""Fit and evaluate routing policies using recorded language admission outcomes."""
import argparse
from hashlib import sha256
import json

import numpy as np
import torch

import facilitator_measured_channel_replies as study
import facilitator_resolution_2719_score as rubric

fit = study.fit
D = fit.D
EVIDENCE = study.EVIDENCE
UPDATES = 96
SOURCES = {
    "afghanistan": (fit.live.EVIDENCE / "results.json", "approved_reply_ids", "record_points"),
    "haiti": (study.dossier.prev.free.source.EVIDENCE / "results.json", "admitted_replies", "points_by_record"),
}


def read(path):
    return json.loads(path.read_text())


def development():
    cases = {}
    for name, (file, replies, points) in SOURCES.items():
        artifact = read(file)
        assert artifact["decoded"] == [0, 1, 2, 3]
        table = np.zeros((4, 4))
        table[:, 0] = 1.
        for reply in artifact[replies]:
            key, question, sent = reply.split("/")
            assert key == "reply" and 0 <= int(question) < 4 and 1 <= int(sent) < 4
            table[int(question), int(sent)] = 1.
        cases[name] = (np.asarray(artifact[points]), table)
    return cases


def train(cases, measured):
    torch.set_num_threads(1)
    estimate = np.mean([v[1] for v in cases.values()], axis=0) if measured else fit.PERFECT
    batch = []
    for public, table in cases.values():
        for name in fit.live.PRIORS:
            prior = fit.ROUTE.TEST_PRIORS[name]
            _, opening = fit.context(public, prior)
            actual = table if measured else fit.PERFECT
            batch.append((*fit.features(public, opening, estimate), opening, fit.value(public, actual)))
    chair, answer, opening, payoff = (torch.as_tensor(np.stack(v), dtype=torch.float64) for v in zip(*batch, strict=True))
    q, r = (torch.nn.Parameter(torch.tensor(w, dtype=torch.float64)) for w in fit.OLD.INITIAL)
    opt = torch.optim.Adam((q, r), lr=.04)
    q_legal, r_legal = map(torch.as_tensor, (D.CHAIR_LEGAL, D.FINAL_LEGAL))
    fees, erased = map(torch.as_tensor, (D.QUERY_COST, fit.ERASURE))
    trace = []
    for step in range(UPDATES + 1):
        asks = (chair @ q).masked_fill(~q_legal, -torch.inf).softmax(-1)
        replies = (answer @ r).masked_fill(~r_legal, -torch.inf).softmax(-1)
        physical = (1 - D.LOSS) * asks + D.LOSS * erased
        path = torch.einsum("nrbm,nmt,nrbtc->nmtc", opening, physical, replies)
        net = torch.einsum("nmtc,nmtc->n", path, payoff) - ((asks @ fees) * opening.sum((1, 2))).sum(1)
        objective = net.mean()
        trace.append({"step": step, "mean_net": float(objective.detach()),
                      "request_rate": float(((1 - asks[..., 0]) * opening.sum((1, 2))).sum(1).mean().detach())})
        if step == UPDATES:
            break
        opt.zero_grad()
        (-objective).backward()
        assert all(torch.isfinite(p.grad).all() for p in (q, r))
        opt.step()
    return {"feature_channel": estimate.tolist(), "weights": [q.detach().tolist(), r.detach().tolist()], "trace": trace}


def fitting():
    cases = development()
    assert len({tuple(v[0]) for v in cases.values()}) == 1
    return {"training_cases": {name: {"score_bank": a.tolist(), "admissions": b.tolist(),
                                     "source_sha256": sha256(SOURCES[name][0].read_bytes()).hexdigest()}
                               for name, (a, b) in cases.items()},
            "updates_per_arm": UPDATES,
            "policies": {key: train(cases, measured) for key, measured in (("measured", True), ("ideal", False))}}


def evaluate(archive, actual):
    expected = rubric.ceilings(study.dossier.packet()["criteria"])
    banks = [row["score_bank"] for row in archive["training_cases"].values()]
    assert all(expected != b for b in banks)
    points = np.asarray(expected)
    result, sensitivity = {}, {}
    for name in fit.live.PRIORS:
        prior = fit.ROUTE.TEST_PRIORS[name]
        opener, mass = fit.context(points, prior)
        policies = {"exact_held_joint": fit.exact(points, mass, actual),
                    "exact_held_independent": fit.exact(points, mass, actual, independent=True)}
        for key, saved in archive["policies"].items():
            estimate = np.asarray(saved["feature_channel"])
            policies[key + "_fit"] = fit.action_policy(saved["weights"], points, mass, estimate)
            policies[key + "_initial"] = fit.action_policy(fit.OLD.INITIAL, points, mass, estimate)
            policies[key + "_exact"] = fit.exact(points, mass, estimate)
            policies[key + "_independent"] = fit.exact(points, mass, estimate, independent=True)
        comparison = {}
        for key, tail in policies.items():
            row = fit.measure(tail, opener, mass, prior, points, actual)
            row["expected_requests"] = float(mass.sum((0, 1)) @ (tail[0] != 0))
            row["policy"] = [a.tolist() for a in tail]
            comparison[key] = row
            assert row["net"] <= comparison["exact_held_joint"]["net"] + 1e-10
        baseline = comparison["measured_independent"]["net"]
        for row in comparison.values():
            row["gain_over_measured_independent"] = row["net"] - baseline
        result[name] = comparison
        sensitivity[name] = {}
        for question in range(4):
            for card in range(1, 4):
                variant = actual.copy()
                variant[question, card] = 1 - variant[question, card]
                quiet = fit.measure(policies["measured_independent"], opener, mass, prior, points, variant)["net"]
                sensitivity[name][f"{question}/{card}"] = {
                    k: fit.measure(policies[k], opener, mass, prior, points, variant)["net"] - quiet
                    for k in ("measured_fit", "ideal_fit")
                }
    return {"authored_points": expected, "held_admission": actual.tolist(), "policies": result,
            "one_cell_flip_advantage_over_fixed_measured_no_request": sensitivity}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("fit", "evaluate"))
    args = cli.parse_args()
    if args.mode == "fit":
        output = fitting()
    else:
        held = read(EVIDENCE / "admission.json")
        output = evaluate(read(EVIDENCE / "fits.json"), np.asarray(held["matrix"]))
    print(json.dumps(output, ensure_ascii=False, indent=2))
