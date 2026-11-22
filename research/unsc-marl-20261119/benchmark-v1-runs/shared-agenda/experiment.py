"""Exact team-return policy fitting on signed workshop mandates with scarce slots."""
from itertools import product
from pathlib import Path
from statistics import mean
import hashlib
import json

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
RELEASE = HERE.parents[1] / "benchmark-v1.5"
DOCKETS = ("iraq", "syria")
MENUS = ((0,), (0, 1), (0, 2), (0, 1, 2))
TABLES = tuple(product(*MENUS))
STEPS = 300
COST = .06
FIRST_ONLY = .5
D = torch.float64
PAID_ERASURE = (np.arange(3)[:, None, None] > 0) & (np.arange(3)[None, :, None] == 0)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def certify(worlds, visible):
    consistent = [gold for cards, gold in worlds if all(cards[role] == card for role, card in visible.items())]
    assert consistent
    common = set.intersection(*consistent)
    return sorted(common)


def cases():
    rows = json.loads((RELEASE / "cases.json").read_text())
    banks = {}
    for docket in DOCKETS:
        selected = [r for r in rows if r["family"] == docket and r["track"] == "workshop"]
        assert len(selected) == 4
        inputs = []
        for row in selected:
            cards = tuple(desk[0]["text"] for desk in row["owned"])
            gold = set(row["gold"])
            constraints = [card.split(": ")[1].removesuffix(".").split(" = ") for card in cards]
            computed = {option["id"] for option in row["options"] if all(option[k] == v for k, v in constraints)}
            assert (computed or {"IMPASSE"}) == gold
            inputs.append((cards, gold))
        results = []
        for (cards, gold), related in product(inputs, range(4)):
            seen = {role: cards[role] for role in range(2) if related & (1 << role)}
            key = certify(inputs, seen)
            assert set(key) <= gold
            assert not key or related in (1, 3)
            if related == 3:
                assert set(key) == gold
            results.append(dict(cards=cards, visibility=related, accepted=key))
        single = [r for r in results if r["visibility"] == 1]
        assert sum(bool(r["accepted"]) for r in single) / len(single) == FIRST_ONLY
        banks[docket] = results
    # All two-docket combinations have equal warrant availability under each concrete receipt.
    checks = 0
    for a, b in product(banks["iraq"], banks["syria"]):
        for row in (a, b):
            assert all(m in "ABCD" or m == "IMPASSE" for m in row["accepted"])
        checks += 1
    return {"dockets": banks, "agenda_receipt_checks": checks}


def settings(held):
    rng = np.random.default_rng(771 if held else 419)
    rows = []
    for i in range(48 if held else 36):
        margins = rng.dirichlet([3, 2, 2, 3], size=2)
        base = np.outer(*margins)
        if held:
            mode = ("opposite", "same", "independent")[i % 3]
            linked = np.zeros((4, 4))
            target = (0, 2, 1, 3) if mode == "opposite" else (0, 1, 2, 3)
            linked[np.arange(4), target] = margins[0]
            amount = rng.uniform(.2, .75) if mode != "independent" else 0.
            prior = (1 - amount) * base + amount * linked
            prizes = rng.uniform(.45, 1.55, 2)
            links = rng.uniform(.48, .95, (2, 2))
        else:
            mode = "diagonal-mixture"
            perturb = rng.dirichlet([3., 3., 3., 4.])
            prior = .7 * base + .3 * np.diag(perturb)
            prizes = rng.uniform(.65, 1.35, 2)
            links = rng.uniform(.62, .92, (2, 2))
        assert np.isclose(prior.sum(), 1.)
        rows.append(dict(mode=mode, p=prior, prizes=prizes, links=links))
    return rows


def stage(scene):
    prior = scene["p"]
    prizes, links = scene["prizes"], scene["links"]
    features = np.zeros((2, 4, 3, 3, 5))
    allowed = np.zeros((4, 3), dtype=bool)
    for inventory, menu in enumerate(MENUS):
        allowed[inventory, list(menu)] = True
    for role, inventory, receipt, action in product(range(2), range(4), range(3), (1, 2)):
        weights = prior[inventory] if role == 0 else prior[:, inventory]
        feasible = sum(p for other, p in enumerate(weights) if action in MENUS[other]) / weights.sum()
        pr = links[1-role, action-1] * feasible if receipt == 0 else float(receipt == action)
        chance = FIRST_ONLY + (1 - FIRST_ONLY) * pr if role == 0 else (1 - FIRST_ONLY) * pr
        win = prizes[action-1] * links[role, action-1] * chance
        features[role, inventory, receipt, action] = (1., win, prizes[action-1], pr, float(receipt == action))
    wire = np.zeros((3, 3))
    wire[0, 0] = 1
    for action in (1, 2):
        wire[action, action] = links[0, action-1]
        wire[action, 0] = 1 - links[0, action-1]
    pay = np.full((3, 3), -COST) * (1 - np.eye(3)[0, :, None])
    pay = pay - COST * np.array([False, True, True])[None, :]
    for action in (1, 2):
        pay[action] += FIRST_ONLY * prizes[action-1]
        pay[action, action] += (1-FIRST_ONLY) * prizes[action-1] * links[1, action-1]
    return features, allowed, wire, pay


def stage_values(scene, feedback, first, second):
    """Independent branch dispatch over both physical deliveries."""
    total = 0.
    released = 0.
    calls = 0.
    mass = 0.
    for i, j in product(range(4), repeat=2):
        for a in MENUS[i]:
            success = scene["links"][0, a-1] if a else 0.
            first_outcomes = ((a, success), (0, 1-success)) if a else ((0, 1.),)
            for receipt, chance in first_outcomes:
                for b in MENUS[j]:
                    p = scene["p"][i, j] * first[i, a] * chance * second[j, receipt if feedback else 0, b]
                    mass += p
                    delivered = scene["links"][1, b-1] if receipt == b and b else 0.
                    points = scene["prizes"][receipt-1] * (FIRST_ONLY + (1 - FIRST_ONLY) * delivered) if receipt else 0.
                    used = int(bool(a)) + int(bool(b))
                    total += p * (points - COST * used)
                    released += p * points
                    calls += p * used
    assert np.isclose(mass, 1.)
    return dict(net=total, weighted_decisions=released, sends=calls)


def picks(table):
    return np.eye(3)[np.asarray(table)]


def array_values(scene, feedback, first, second):
    _, _, wire, pay = stage(scene)
    if not feedback:
        second = np.repeat(second[:, :1], 3, axis=1)
    joint = np.einsum("ij,ia,ar,jrb->arb", scene["p"], first, wire, second)
    assert np.isclose(joint.sum(), 1.)
    return float(np.sum(joint * (pay[None, :, :] - COST * PAID_ERASURE)))


def exact(scene, feedback):
    _, _, wire, pay = stage(scene)
    best = (-float("inf"), None)
    for table in TABLES:
        first = picks(table)
        if feedback:
            # Best response under the same private inventory and receipt.
            values = np.einsum("ij,ia,ar,rb->jrb", scene["p"], first, wire, pay)
            second = tuple(tuple(max(MENUS[j], key=lambda b: values[j, r, b]) for r in range(3)) for j in range(4))
            options = (second,)
        else:
            options = (tuple((b, b, b) for b in second) for second in TABLES)
        for second in options:
            score = 0.
            for i, j in product(range(4), repeat=2):
                a = table[i]
                for r, p in enumerate(wire[a]):
                    b = second[j][r if feedback else 0]
                    score += scene["p"][i, j] * p * (pay[r, b] - COST * bool(a and not r))
            if score > best[0] + 1e-10:
                best = (score, (first, picks(second)))
    measured = stage_values(scene, feedback, *best[1])
    assert np.isclose(best[0], measured["net"])
    assert np.isclose(best[0], array_values(scene, feedback, *best[1]))
    return measured, best[1]


def scripted(scene, feedback):
    features, _, _, _ = stage(scene)
    follower = picks(tuple(tuple(r if r in opts and r and
                                 (1 - FIRST_ONLY) * scene["prizes"][r-1] * scene["links"][1, r-1] > COST else 0
                                 for r in range(3)) for opts in MENUS))
    slate = {"wait": (picks([0]*4), picks([[0]*3]*4))}
    for rank in ((1, 2), (2, 1), (1,), (2,), ()):
        table = picks(tuple(next((a for a in rank if a in opts), 0) for opts in MENUS))
        slate["rank-" + "".join(map(str, rank))] = (table, follower if feedback else
                                                    np.repeat(table[:, None, :], 3, axis=1))
    local = []
    for role in range(2):
        local.append(picks(tuple(max(MENUS[i], key=lambda a: features[role, i, 0, a, 1] - COST * bool(a))
                                 for i in range(4))))
    slate["local-conditional"] = (local[0], follower if feedback else np.repeat(local[1][:, None, :], 3, axis=1))
    return slate


def batch(scenes):
    features, masks, links, yields = map(np.stack, zip(*(stage(s) for s in scenes), strict=True))
    p = np.stack([row["p"] for row in scenes])
    y = yields[:, None, :, :] - COST * PAID_ERASURE[None, :, :, :]
    return (torch.as_tensor(x) for x in (features, masks, links, y, p))


def actions(x, mask, w, greedy):
    scores = torch.einsum("kvirbf,vf->kvirb", x, w).masked_fill(~mask[:, None, :, None, :], -torch.inf)
    if greedy:
        return torch.nn.functional.one_hot(scores.argmax(-1), 3).to(D)
    return scores.softmax(-1)


def fit(scenes, feedback):
    x, mask, link, y, p = batch(scenes)
    w = torch.zeros((2, 5), dtype=D, requires_grad=True)
    optimizer = torch.optim.Adam([w], lr=.03)

    def expected():
        probs = actions(x, mask, w, False)
        first = probs[:, 0, :, 0]
        second = probs[:, 1] if feedback else probs[:, 1, :, :1].expand(-1,-1,3,-1)
        net = torch.einsum("kij,kia,kar,kjrb,karb->k", p, first, link, second, y)
        return net, first, second

    initial = float(expected()[0].detach().mean())
    start, first, second = expected()
    for k, (a, b) in enumerate(zip(first, second, strict=True)):
        assert abs(float(start[k].detach()) - stage_values(scenes[k], feedback, a.detach().numpy(),
                                                           b.detach().numpy())["net"]) < 1e-10
    for _ in range(STEPS):
        optimizer.zero_grad()
        objective = expected()[0].mean() - .001 * w.square().mean()
        (-objective).backward()
        optimizer.step()
    return w.detach(), dict(start=initial, end=float(expected()[0].detach().mean()))


def experiment(training, held, feedback):
    weight, objective = fit(training, feedback)
    x, mask, _, _, _ = batch(held)
    greedy = actions(x, mask, weight, True).numpy()
    sampled = actions(x, mask, weight, False).numpy()
    outcomes = []
    for idx, scene in enumerate(held):
        controls = scripted(scene, feedback)
        result = {name: stage_values(scene, feedback, *pair) for name, pair in controls.items()}
        candidates = [name for name in controls if name.startswith("rank")]
        reference = max(candidates, key=lambda name: result[name]["net"])
        fixed0, fixed1 = controls[reference]
        first, second = greedy[idx, 0, :, 0], greedy[idx, 1]
        extra = {
            "learned": (first, second),
            "sampled": (sampled[idx, 0, :, 0], sampled[idx, 1]),
            "learned-first": (first, fixed1),
            "learned-second": (fixed0, second),
        }
        result.update({name: stage_values(scene, feedback, *pair) for name, pair in extra.items()})
        result["best-rank"] = result[reference]
        result["exact"], oracle = exact(scene, feedback)
        for name, stats in result.items():
            assert stats["net"] <= result["exact"]["net"] + 1e-10, (name, idx)
        outcomes.append(dict(regime=scene["mode"], reference=reference, scores=result,
                             local=first.argmax(-1).tolist(), second=second.argmax(-1).tolist(),
                             exact=tuple(x.argmax(-1).tolist() for x in oracle)))
    avg = {k: {m: mean(row["scores"][k][m] for row in outcomes) for m in ("net", "weighted_decisions", "sends")}
           for k in outcomes[0]["scores"]}
    margins = [row["scores"]["learned"]["net"] - row["scores"]["best-rank"]["net"] for row in outcomes]
    return dict(weights=weight.tolist(), fit=objective, means=avg,
                versus_best_rank=dict(wins=int(sum(m > 1e-10 for m in margins)), ties=int(sum(abs(m) <= 1e-10 for m in margins)),
                                      losses=int(sum(m < -1e-10 for m in margins))), held=outcomes)


def run():
    torch.set_num_threads(1)
    training, held = settings(False), settings(True)
    return dict(release=digest(RELEASE / "release.json"), source=digest(RELEASE / "cases.json"),
                protocol=digest(HERE / "protocol.md"), certification=cases(), training_updates_per_fit=STEPS,
                simultaneous=experiment(training, held, False), sequential=experiment(training, held, True))


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
