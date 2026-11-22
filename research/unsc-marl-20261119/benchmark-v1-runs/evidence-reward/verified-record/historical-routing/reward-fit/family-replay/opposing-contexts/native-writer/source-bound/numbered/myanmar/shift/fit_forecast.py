"""Jointly optimize the routing heads with partial forecast inputs and true shared reward."""
from hashlib import sha256
from itertools import product
from pathlib import Path
import json

import numpy as np
import torch

import shift_audit as audit

s, m, n = audit.s, audit.m, audit.n
j, o, D = m.data.training, m.o, m.D
HERE = Path(__file__).resolve().parent
UPDATES = 120


def fit(banks, opener_params):
    tm, features, predict, truth = [], [], [], []
    for bank, prior in product(banks, o.R.TEST_PRIORS.values()):
        actual = np.array(bank, dtype=float)
        singleton = s.t.cal.estimated(actual)
        opening = o.replan.study.opening(singleton, prior, opener_params)
        mass = o.opening(*opening, prior)
        for observed in s.forecasts(singleton, actual[s.PAIR]):
            tm.append(mass)
            features.append(j.router_features(observed, mass))
            predict.append(o.payoff(observed))
            truth.append(o.payoff(actual))
    mass, router, predicted, actual = (torch.from_numpy(np.stack(v)) for v in (tm, features, predict, truth))
    assert tuple(router.shape) == (1296, 8, 4, 4)
    torch.set_num_threads(1)
    q_head = torch.nn.Parameter(torch.tensor([1., 0., -.05, 0.], dtype=torch.float64))
    a_head = torch.nn.Parameter(torch.tensor([1., .1, 0., 0.], dtype=torch.float64))
    opt = torch.optim.Adam((q_head, a_head), lr=.06)
    chair_legal, reply_legal = map(torch.from_numpy, (D.CHAIR_LEGAL, D.FINAL_LEGAL))
    fee = torch.from_numpy(D.QUERY_COST)
    erasure = torch.from_numpy(j.fit.ERASURE)
    flag = torch.as_tensor(j.reply_templates(), dtype=torch.float64)
    mask_probability = mass.sum((1, 2))
    trace = []

    def reward_by_reply(observed, payoff):
        return torch.einsum("nrbm,nmt,nmtc->nrbtc", mass, observed, payoff)

    for step in range(UPDATES + 1):
        q_temp = .70 - .55 * step / UPDATES
        a_temp = .45 - .35 * step / UPDATES
        query = ((router @ q_head) / q_temp).masked_fill(~chair_legal, -torch.inf).softmax(-1)
        heard = (1 - D.LOSS) * query + D.LOSS * erasure
        subjective = reward_by_reply(heard, predicted)
        frequency = torch.einsum("nrbm,nmt->nrbt", mass, heard)
        advantage = (subjective - subjective[..., :1]) / frequency.clamp_min(1e-12)[..., None] / 10.
        logits = (advantage * a_head[0] + flag @ a_head[1:]) / a_temp
        reply = logits.masked_fill(~reply_legal, -torch.inf).softmax(-1)
        reward = ((reply * reward_by_reply(heard, actual)).sum((1, 2, 3, 4))
                  - ((query @ fee) * mask_probability).sum(1)).mean()
        if step % 20 == 0:
            trace.append({"update": step, "true_reward": float(reward.detach()),
                          "query_rate": float(((1 - query[..., 0]) * mask_probability).sum(1).detach().mean())})
        if step == UPDATES:
            break
        opt.zero_grad()
        (-reward).backward()
        assert all(torch.isfinite(weight.grad).all() for weight in (q_head, a_head))
        opt.step()
    weights = tuple(weight.detach().numpy() for weight in (q_head, a_head))
    return weights, trace


def run():
    dense_path, sparse_path = m.HERE.parents[1] / "fit.json", m.HERE.parent / "sparse-results.json"
    original_fit, sparse = n.read(dense_path), n.read(sparse_path)
    old = n.read(o.replan.study.OLD)["training"]["budget_fit"]
    training = sparse["training"]
    tests = audit.cases(original_fit, sparse)
    assert not {tuple(x) for x in training} & {tuple(b) for _, _, b in tests}
    new, trace = fit(training, old)
    parameters = (new, [np.array(p) for p in sparse["parameters"]])
    frozen = n.read(HERE / "results.json")
    expected = {(r["suite"], r["case"], r["prior"], r["prior_information"], r["review_offset"]): r
                for r in frozen["runs"]}
    rows = []
    for (suite, case, bank), (tag, (truth, proxy)), info, offset in product(
            tests, audit.laws().items(), ("correct_mixture", "dominant_only"), (-7, 0, 7)):
        previous = expected.pop((suite, case, tag, info, offset))
        assert previous["bank"] == bank.tolist()
        value = audit.evaluate(bank, truth, truth if info == "correct_mixture" else proxy,
                               bank[s.PAIR] + offset, parameters, old)
        assert value["exact_margin"] == previous["exact_margin"]
        rows.append({k: previous[k] for k in ("suite", "case", "bank", "prior",
                                               "prior_information", "review_offset")} | value)
    assert len(rows) == 360 and not expected
    pins = (Path(__file__), HERE / "training-protocol.md", HERE / "results.json", Path(audit.__file__),
            dense_path, sparse_path, Path(j.__file__))
    return {"updates": UPDATES, "parameter_shapes": [list(x.shape) for x in new],
            "weights": [x.tolist() for x in new], "training_banks": len(training), "trace": trace,
            "runs": rows, "summary": audit.summarize(rows),
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in pins}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
