"""Learn to use the exact public proof status of a delivered mandate."""
import json
from statistics import mean

import numpy as np
import torch

import experiment as e

# 1 and 2 need another card. 3 and 4 certify Iraq and Syria already.
RECEIPTS = (0, 1, 2, 1, 2)


def stage(scene):
    feat, mask, ordinary, _ = e.stage(scene)
    flags = np.array([0., 0., 0., 1., 1.])
    expanded = np.zeros((2, 4, 5, 3, 6))
    expanded[..., :5] = feat[:, :, RECEIPTS]
    expanded[..., 5] = flags[None, None, :, None]
    expanded[..., 5] *= np.array([0., 1., 1.])[None, None, None, :]
    wire = np.column_stack((ordinary[:, 0], ordinary[:, 1:]*(1-e.FIRST_ONLY), ordinary[:, 1:]*e.FIRST_ONLY))
    pay = np.zeros((3, 5, 3))
    send = np.arange(3) > 0
    cost = e.COST * (send[:, None, None].astype(float) + send[None, None, :])
    for r, docket in enumerate(RECEIPTS):
        if r >= 3:
            pay[:, r, :] = scene["prizes"][docket-1]
        elif r:
            pay[:, r, docket] = scene["prizes"][docket-1]*scene["links"][1, docket-1]
    assert np.allclose(wire.sum(-1), 1.)
    return expanded, mask, wire, pay, pay - cost


def outcomes(scene, first, second):
    # Independent replay from the original deliveries and warrant probabilities.
    values = dict(net=0., weighted_decisions=0., sends=0., redundant=0.)
    mass = 0.
    for i, j in np.ndindex(4, 4):
        for a in e.MENUS[i]:
            prior = scene["p"][i, j] * first[i, a]
            if a:
                delivered = scene["links"][0, a-1]
                events = ((0, 1-delivered), (a, delivered*(1-e.FIRST_ONLY)), (a+2, delivered*e.FIRST_ONLY))
            else:
                events = ((0, 1.),)
            for r, p in events:
                for b in e.MENUS[j]:
                    reach = prior * p * second[j, r, b]
                    mass += reach
                    verified = r >= 3
                    points = 0.
                    if verified:
                        points = scene["prizes"][a-1]
                    elif r and a == b:
                        points = scene["prizes"][a-1]*scene["links"][1, b-1]
                    sends = int(bool(a)) + int(bool(b))
                    values["weighted_decisions"] += reach * points
                    values["sends"] += reach * sends
                    values["redundant"] += reach * int(bool(b) and (not r or verified or a != b))
                    values["net"] += reach * (points - e.COST*sends)
    assert np.isclose(mass, 1.)
    return values


def tensor_batch(scenes):
    x, mask, wire, _, utility = map(np.stack, zip(*(stage(s) for s in scenes), strict=True))
    return tuple(torch.as_tensor(a) for a in (x, mask, wire, utility, np.stack([s["p"] for s in scenes])))


def fit(scenes):
    x, mask, wire, utility, prior = tensor_batch(scenes)
    w = torch.zeros((2, 6), dtype=e.D, requires_grad=True)
    optimizer = torch.optim.Adam([w], lr=.03)

    def returns():
        prob = e.actions(x, mask, w, False)
        first, second = prob[:, 0, :, 0], prob[:, 1]
        score = torch.einsum("kij,kia,kar,kjrb,karb->k", prior, first, wire, second, utility)
        return score, first, second

    start, first, second = returns()
    for idx, s in enumerate(scenes):
        assert np.isclose(float(start[idx].detach()),
                          outcomes(s, first[idx].detach().numpy(), second[idx].detach().numpy())["net"])
    for _ in range(e.STEPS):
        optimizer.zero_grad()
        loss = -returns()[0].mean() + .001 * w.square().mean()
        loss.backward()
        optimizer.step()
    return w.detach(), [float(start.detach().mean()), float(returns()[0].detach().mean())]


def fixed(scene):
    _, _, wire, _, utility = stage(scene)
    # No positive return is possible from a report if the chair already has a proof.
    follower = e.picks(tuple(tuple(r if r in menu and r in (1, 2)
                                   and scene["prizes"][r-1]*scene["links"][1, r-1] > e.COST else 0
                                   for r in range(5)) for menu in e.MENUS))
    choices = np.einsum("ij,ar,jrb,arb->ia", scene["p"], wire, follower, utility)
    first = e.picks(tuple(max(menu, key=lambda a: choices[i, a]) for i, menu in enumerate(e.MENUS)))
    answer = outcomes(scene, first, follower)
    for table in e.TABLES:
        alternative = outcomes(scene, e.picks(table), follower)
        assert alternative["net"] <= answer["net"] + 1e-10
    return first, follower


def run():
    torch.set_num_threads(1)
    train, held = e.settings(False), e.settings(True)
    earlier_path = e.HERE / "results.json"
    earlier = json.loads(earlier_path.read_text())["sequential"]
    w, fit_return = fit(train)
    x, mask, _, _, _ = tensor_batch(held)
    learned = e.actions(x, mask, w, True).numpy()
    sampled = e.actions(x, mask, w, False).numpy()
    rows = []
    for idx, s in enumerate(held):
        f, g = fixed(s)
        old = earlier["held"][idx]
        a = e.picks(old["local"])
        b = e.picks([tuple(row[r] for r in RECEIPTS) for row in old["second"]])
        l, m = learned[idx, 0, :, 0], learned[idx, 1]
        arms = {"fixed": (f, g), "receipt-only": (a, b), "learned": (l, m),
                "sampled": (sampled[idx, 0, :, 0], sampled[idx, 1]),
                "fixed-follow-on": (l, g), "fixed-opening": (f, m)}
        scores = {name: outcomes(s, *pair) for name, pair in arms.items()}
        assert np.isclose(scores["receipt-only"]["net"], old["scores"]["learned"]["net"])
        assert all(val["net"] <= scores["fixed"]["net"] + 1e-10 for val in scores.values())
        first, second = (l.argmax(-1).tolist(), m.argmax(-1).tolist())
        rows.append(dict(scores=scores, first=first, second=second, fixed_first=f.argmax(-1).tolist()))
    metrics = {arm: {k: mean(row["scores"][arm][k] for row in rows) for k in rows[0]["scores"][arm]}
               for arm in rows[0]["scores"]}
    return dict(protocol=e.digest(e.HERE / "proof-feedback-protocol.md"), prior=e.digest(earlier_path),
                fit_updates=e.STEPS, train_stochastic_return=fit_return, weights=w.tolist(), held=rows,
                means=metrics)


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
