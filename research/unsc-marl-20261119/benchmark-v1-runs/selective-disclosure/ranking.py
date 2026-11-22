"""Use within-state joint return differences to fit the recipient."""
from itertools import combinations, permutations
import json
from statistics import mean
from unittest.mock import patch

import numpy as np
import torch

import family_transfer as exact
import joint_opener as opener
import recipient as old
import selective as s

HERE, shared, base = s.HERE, s.shared, s.base
ARMS = ("fixed", "value-fit", "rank-fit", "checked-rank", "exact-recipient")


def fit(tables):
    samples = []
    for table in tables:
        for row in table.values():
            for a, b in combinations(range(3), 2):
                advantage = row["true"][a]-row["true"][b]
                if abs(advantage) <= 1e-10:
                    continue
                sign = np.sign(advantage)
                samples.append((sign*(row["x"][a]-row["x"][b]), sign*(row["informed"][a]-row["informed"][b]),
                                abs(advantage)*row["weight"]))
    diff, forecast, weight = (torch.tensor(np.stack(a), dtype=torch.float64) for a in zip(*samples, strict=True))
    weight /= weight.sum()
    w = torch.zeros(diff.shape[1], dtype=torch.float64, requires_grad=True)
    opt = torch.optim.Adam([w], lr=.03)

    def loss():
        error = torch.nn.functional.softplus(-(forecast+diff@w)/.04)
        return weight @ error + .02*w.square().mean()

    start = float(loss().detach())
    for _ in range(160):
        opt.zero_grad()
        loss().backward()
        opt.step()
    return w.detach().numpy(), dict(pairs=len(samples), initial_loss=start, final_loss=float(loss().detach()))


def measure(d, initial, table, rank, value):
    choices = {}
    for arm in ARMS:
        p = initial.copy()
        override = 0.
        regret = 0.
        predicted = 0.
        for key, row in table.items():
            incumbent = int(row["informed"].argmax())
            default = row["informed"]
            runtimes = {"fixed": default, "value-fit": default+row["x"]@value, "rank-fit": default+row["x"]@rank,
                        "checked-rank": default+row["x"]@rank, "exact-recipient": row["true"]}
            action = int(runtimes[arm].argmax())
            if arm == "checked-rank" and default[incumbent]-default[action] > .02+1e-10:
                action = incumbent
            p[d.states[key]] = 0.
            p[d.states[key], action] = 1.
            override += (action != incumbent)*row["weight"]
            regret += (row["true"].max()-row["true"][action])*row["weight"]
            predicted += row["true"][action]*row["weight"]
        stats = s.measure(d, p, base.FEE)
        assert abs(predicted - stats["after_followup"]) < 1e-9
        choices[arm] = (p, stats | {"override_mass": override, "recipient_regret": regret})
    upper = choices["exact-recipient"][1]["net"]
    for _, r in choices.values():
        assert abs(upper-r["net"]-r["recipient_regret"]) < 1e-9
    return choices


def run():
    torch.set_num_threads(1)
    registry = s.read(s.original.REGISTRY)
    lookup = {p["draw"]: p for p in registry["accepted"]}
    archived = s.read(s.FIT)
    opener_artifact = s.read(HERE / "joint-opener.json")
    value_artifact = s.read(HERE / "recipient.json")
    old_w = torch.tensor(archived["weights"], dtype=torch.float64)
    first_w = np.asarray(opener_artifact["weights"])
    value_w = np.asarray(value_artifact["weights"])
    prose = s.read(s.PROSE)
    mapping = {tuple(r["intended"]): tuple(r["evidence_reader"]) for r in prose["messages"]}
    costs = {tuple(r["intended"]): (r["tokens"]["writer"], r["tokens"]["evidence"]) for r in prose["messages"]}

    def select(draw):
        with patch.dict(shared.FIXTURES, {"target": s.original.fixture(lookup[draw])}):
            return shared.Grid("target")

    def stage(grid, balanced):
        d = shared.Experiment(grid, balanced)
        for i, role in enumerate(d.roles):
            if role == 2:
                d.mask[i, 1:] = False
        default = d.probabilities(old_w).numpy()
        first = opener.choose(d, default, opener.basis(d, d.prior, default), first_w, base.FEE, "joint-fitted")
        return d, first, old.aggregate(d, first)

    w, training = fit([stage(select(i), True)[2] for i in registry["partition"]["fit"]])

    def episode(grid, balanced, statements):
        d, first, table = stage(grid, balanced)
        options = measure(d, first, table, w, value_w)
        scores = {arm: r[1] for arm, r in options.items()}
        assert scores["exact-recipient"]["net"] <= exact.solve(d, True)["net"]+1e-9
        out = {"scores": scores}
        if statements:
            audit = {name: s.ledger_metrics(d, row[0], mapping, costs) for name, row in options.items()}
            assert all(abs(r["net"]-scores[name]["net"]) < 1e-9 for name, r in audit.items())
            out["language"] = audit
        return out

    outcomes = {}
    for mode, balanced in (("balanced", True), ("uniform-stress", False)):
        outcomes[mode] = {}
        for label in ("space-reserved", "mali", "myanmar"):
            if label == "space-reserved":
                rows = [dict(case=i, **episode(select(i), balanced, True)) for i in registry["partition"]["reserved"]]
            else:
                rows = [dict(order=order, **episode(shared.Grid(label, order), balanced, False))
                        for order in permutations(range(3))]
            reference = value_artifact["results"][mode][label]["conditions"]
            for received, prior in zip(rows, reference, strict=True):
                for fresh, archive in (("fixed", "policy-aware"), ("value-fit", "fitted")):
                    assert abs(received["scores"][fresh]["net"]-prior["metrics"][archive]["net"]) < 1e-9
            macro = {name: {key: mean(row["scores"][name][key] for row in rows)
                            for key in ("net", "override_mass", "recipient_regret")} for name in ARMS}
            outcomes[mode][label] = dict(macro=macro, rows=rows)
    from hashlib import sha256
    inputs = (HERE / "ranking-protocol.md", HERE / "recipient.json", HERE / "joint-opener.json")
    return dict(training=training, coef=w.tolist(), results=outcomes,
                pins={p.name: sha256(p.read_bytes()).hexdigest() for p in inputs})


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
