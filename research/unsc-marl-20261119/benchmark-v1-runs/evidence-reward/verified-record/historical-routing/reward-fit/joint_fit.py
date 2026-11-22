"""Optimize historical request and reply heads for released points after message costs."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np
import torch

import objective as o

HERE = Path(__file__).resolve().parent
D, R, fit, e, opening = o.D, o.R, o.fit, o.e, o.opening
SEED, UPDATES, TRAIN, HOLD = 814, 120, 144, 36


def draw_banks(rng, count):
    masks = (np.arange(8)[:, None] & np.array((1, 2, 4))) != 0
    pair = np.stack([masks[:, i] & masks[:, j] for i, j in ((0, 1), (0, 2), (1, 2))], axis=1)
    banks = set()
    while len(banks) < count:
        singles = rng.integers(1, 18, size=3)
        pairs = rng.integers(0, 11, size=3)
        cap = int(rng.integers(8, 46))
        points = masks @ singles + pair @ pairs
        points[7] += rng.integers(0, 7)
        bank = np.minimum(cap, points)
        banks.add(tuple(map(int, bank)))
    return sorted(banks)


def router_features(points, mass):
    values = o.payoff(points)
    trial = D.one_hot(D.scripts()[3])
    if_asked = np.einsum("rbm,rbtc,mtc->mt", mass, trial, values)
    visits = mass.sum((0, 1))
    rate = np.einsum("rbm,rt->mt", mass, R.SEND) / np.maximum(visits[:, None], 1e-12)
    delta = (1 - D.LOSS) * (if_asked - if_asked[:, :1]) / np.maximum(visits[:, None], 1e-12)
    cost = np.broadcast_to(D.QUERY_COST, delta.shape)
    nonzero = np.broadcast_to(np.arange(4) != 0, delta.shape)
    return np.stack((delta / 10., rate * nonzero, nonzero, cost), axis=-1)


def reply_templates():
    question, reply = np.ix_(np.arange(4), np.arange(4))
    earlier, candidate = np.ix_(np.arange(4), np.arange(4))
    return np.stack((np.broadcast_to((question == reply) & (question != 0), (8, 4, 4, 4)),
                     np.broadcast_to(((earlier == candidate) & (candidate != 0))[:, None, :], (8, 4, 4, 4)),
                     np.broadcast_to(candidate != 0, (8, 4, 4, 4))), axis=-1)


def response_values(points, mass, q):
    observed = fit.heard(D.one_hot(q))
    weighted = np.einsum("rbm,mt,mtc->rbtc", mass, observed, o.payoff(points))
    visit = np.einsum("rbm,mt->rbt", mass, observed)
    return ((weighted - weighted[..., :1]) / np.maximum(visit[..., None], 1e-12)) / 10


def learn(banks, original):
    torch.set_num_threads(1)
    batch = []
    for values, law in product(banks, R.TEST_PRIORS.values()):
        points = np.array(values, dtype=float)
        a, b = o.replan.study.opening(points, law, original)
        mass = opening(a, b, law)
        batch.append((router_features(points, mass), mass, o.payoff(points)))
    router, public, reward = (torch.from_numpy(np.stack(x)) for x in zip(*batch, strict=True))
    q_head = torch.nn.Parameter(torch.tensor([1., 0., -.05, 0.], dtype=torch.float64))
    a_head = torch.nn.Parameter(torch.tensor([1., .1, 0., 0.], dtype=torch.float64))
    opt = torch.optim.Adam((q_head, a_head), lr=.06)
    mask_q, mask_a = map(torch.from_numpy, (D.CHAIR_LEGAL, D.FINAL_LEGAL))
    fee = torch.from_numpy(D.QUERY_COST)
    erased = torch.from_numpy(fit.ERASURE)
    flags = torch.tensor(reply_templates(), dtype=torch.float64)
    first_mass = public.sum((1, 2))
    trace = []
    for iteration in range(UPDATES + 1):
        q_temp = .70 - .55 * iteration / UPDATES
        a_temp = .45 - .35 * iteration / UPDATES
        choices = ((router @ q_head) / q_temp).masked_fill(~mask_q, -torch.inf).softmax(-1)
        heard = (1 - D.LOSS) * choices + D.LOSS * erased
        if_respond = torch.einsum("nrbm,nmt,nmtc->nrbtc", public, heard, reward)
        visit = torch.einsum("nrbm,nmt->nrbt", public, heard)
        gain = (if_respond - if_respond[..., :1]) / visit.clamp_min(1e-12)[..., None] / 10.
        logits = (gain * a_head[0] + flags @ a_head[1:]) / a_temp
        responses = logits.masked_fill(~mask_a, -torch.inf).softmax(-1)
        net = ((responses * if_respond).sum((1, 2, 3, 4)) - ((choices @ fee) * first_mass).sum(1)).mean()
        if iteration % 20 == 0:
            trace.append({"update": iteration, "net_before_opening_cost": float(net.detach()),
                          "query_rate": float(((1. - choices[..., 0]) * first_mass).sum(1).mean().detach())})
        if iteration == UPDATES:
            break
        opt.zero_grad()
        (-net).backward()
        assert all(torch.isfinite(v.grad).all() for v in (q_head, a_head))
        opt.step()
    return (q_head.detach().numpy(), a_head.detach().numpy()), trace


def paired(points, mass, params):
    q_head, a_head = params
    preferred = router_features(points, mass) @ q_head
    q = np.where(D.CHAIR_LEGAL, preferred, -np.inf).argmax(-1)
    a_values = response_values(points, mass, q) * a_head[0] + reply_templates() @ a_head[1:]
    return q, np.where(D.FINAL_LEGAL, a_values, -np.inf).argmax(-1)


def summary(points, law, openers, mass, params):
    q, reply = paired(points, mass, params)
    trained = o.measure(points, mass, law, openers, (q, reply))
    exact_partner = o.measure(points, mass, law, openers, (q, o.choose_response(q, mass, points)))
    quiet = np.zeros_like(q)
    learned_quiet = o.measure(points, mass, law, openers, (quiet, paired_quiet(points, mass, params, quiet)))
    all_rows = {"joint_fit": trained, "fitted_chair_exact_reply": exact_partner, "learned_no_request": learned_quiet}
    all_rows |= o.controls(points, mass, law, openers)
    optimum = all_rows["exact_ask_reply"]["net"]
    assert all(v["net"] <= optimum + 1e-9 for v in all_rows.values())
    return all_rows


def paired_quiet(points, mass, params, q):
    a_head = params[1]
    x = response_values(points, mass, q) * a_head[0] + reply_templates() @ a_head[1:]
    return np.where(D.FINAL_LEGAL, x, -np.inf).argmax(-1)


def run():
    rng = np.random.default_rng(SEED)
    # One frozen draw for both data splits. A bank tuple cannot occur on both sides.
    banks = draw_banks(rng, TRAIN + HOLD)
    indices = rng.permutation(len(banks))
    train = [banks[i] for i in indices[:TRAIN]]
    test = [banks[i] for i in indices[TRAIN:]]
    previous = o.replan.study
    original = e.read(previous.OLD)["training"]["budget_fit"]
    params, trace = learn(train, original)
    held = {}
    for endpoint, label, points, law, openers, mass, archived in o.historical():
        centered = tuple(points - points[0])
        assert centered not in banks
        rows = summary(points, law, openers, mass, params)
        details = {k: archived[k]["net"] for k in ("learned", "same_responder_silence", "fixed_3")}
        held.setdefault(endpoint, {})[label] = {"rows": rows, "archived_net": details}
    synthetic = {}
    for i, (values, law_label) in enumerate(product(test, R.TEST_PRIORS)):
        law = R.TEST_PRIORS[law_label]
        points = np.array(values, dtype=float)
        openers = previous.opening(points, law, original)
        rows = summary(points, law, openers, opening(*openers, law), params)
        synthetic[str(i)] = {"bank": values, "law": law_label, "net": {key: row["net"] for key, row in rows.items()}}
    files = (Path(__file__), Path(o.__file__), HERE / "protocol.md", HERE.parent / "results.json", previous.OLD)
    return {"seed": SEED, "updates": UPDATES, "train_banks": train, "holdout_banks": test,
            "trace": trace, "parameters": [v.tolist() for v in params], "historical": held,
            "synthetic_holdout": synthetic, "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
