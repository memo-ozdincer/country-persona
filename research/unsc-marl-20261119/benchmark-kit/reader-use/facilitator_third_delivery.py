"""Fit three-slot documentary policies with a receipt-aware chair request."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

import facilitator_guard_calibrated_fit as archive
import source_request_policy as route

HERE = Path(__file__).resolve().parent
UPDATES = 240
LOSS = .10
COMPLETE_BONUS = 21.
CHAIR_LEGAL = route.ASK
QUERY_COST = route.SIGNAL_COST * (route.ACTIONS != 0)
SEND_COST = route.DELIVERY_COST * (route.ACTIONS != 0)
FINAL_LEGAL = route.SEND[:, None, None, :]


def data():
    prior = archive.training_banks()
    fitting = {name: row for name, row in prior.items() if name in ("outer_space", "mali", "climate")}
    for order in range(3):
        weights = np.roll(np.array([8, 12, 16]), order)
        bank = [34 + sum(weights[i] for i in range(3) if mask & (1 << i)) for mask in range(8)]
        fitting[f"authored_full_{order}"] = {"guarded": [int(x) for x in bank],
                                              "source": "Authored additive control with all three cards required."}
    held = {}
    for family, location in (("unifil", "unifil-final-transfer/verified-transport.json"),
                             ("myanmar", "myanmar-sponsorship-probe/score.json")):
        path = archive.ARCHIVE / location
        source = archive.load(path)
        if family == "unifil":
            rows = [source["bank"][f"team-{m}"] for m in range(8)]
            scores = [r["release_points"] for r in rows]
            assert all((r["release_points"] == 70) == r["strict_complete"] for r in rows)
        else:
            scores = source["revised_points"]
            assert [r["points"] for r in source["records"]] == scores
            assert all((r["points"] == 70) == r["complete"] for r in source["records"])
        assert scores[-1] == 70 and max(scores[:-1]) < 70
        held[family] = {"path": str(path), "sha256": sha256(path.read_bytes()).hexdigest(), "guarded": scores,
                        "evidence": "Archived generated records and source-reviewed rubric."}
    sentence = HERE / "facilitator-modular-record-evidence/complete-sentences.json"
    for family, row in archive.load(sentence)["results"].items():
        scores = [row["records"][f"normalized/{m}"]["guarded_points"] for m in range(8)]
        held[family] = {"path": str(sentence), "sha256": sha256(sentence.read_bytes()).hexdigest(),
                        "guarded": scores, "evidence": "Archived same-assistant-reviewed modular writer."}
    assert not set(fitting) & held.keys()
    return fitting, held


def transitions():
    first = np.zeros((4, 4, 8))
    last = np.zeros((8, 4, 8))
    for a, b, ok_a, ok_b in product(range(4), range(4), (0, 1), (0, 1)):
        first[a, b, route.BITS[a] * ok_a | route.BITS[b] * ok_b] += (
            (1 - LOSS if ok_a else LOSS) * (1 - LOSS if ok_b else LOSS))
    for m, c in product(range(8), range(4)):
        last[m, c, m] += LOSS
        last[m, c, m | route.BITS[c]] += 1 - LOSS
    assert np.allclose(first.sum(-1), 1) and np.allclose(last.sum(-1), 1)
    return first, last


FIRST, LAST = transitions()


def one_hot(actions):
    return np.eye(4)[actions]


def distribution(policy, prior, erase=False):
    left, right, chair, reply = policy
    opening = np.einsum("lr,la,rb,abm->rbm", prior, one_hot(left), one_hot(right), FIRST)
    queries = opening.sum(axis=(0, 1)) @ QUERY_COST[chair]
    observed = (1 - LOSS) * one_hot(chair) + LOSS * np.eye(4)[0]
    if erase:
        observed = np.broadcast_to(np.eye(4)[0], observed.shape)
    end = np.einsum("rbm,mq,rbqc->mc", opening, observed, one_hot(reply))
    mass = np.einsum("mc,mcn->n", end, LAST)
    costs = queries + prior.sum(1) @ SEND_COST[left] + prior.sum(0) @ SEND_COST[right] + end.sum(0) @ SEND_COST
    assert np.isclose(mass.sum(), 1)
    return mass, float(costs)


def measure(policy, prior, points, erase=False):
    mass, fee = distribution(policy, prior, erase)
    material = float(mass @ points)
    strict = float(mass @ (points == 70))
    return {"guarded_points": material, "strict_complete": strict, "cost": fee,
            "net": material + COMPLETE_BONUS * strict - fee,
            "receipt_mass": mass.tolist()}


def train(fitting, independent):
    import torch

    torch.set_num_threads(1)
    rng = torch.Generator().manual_seed(route.SEED)
    bank, weights = archive.training_values(fitting, "guarded")
    # Recover each bank's public offset for the strict flag. Centering
    # changes the derivative only by a constant and keeps fees in points.
    bonus = []
    for case in fitting.values():
        for order in archive.calibrated_orders(case["guarded"]):
            points = archive.unama.reordered(case["guarded"], order)
            bonus.append((points == 70) * COMPLETE_BONUS)
    values = np.asarray(weights) @ (np.asarray(bank) + np.asarray(bonus))
    prior = torch.as_tensor(route.TEST_PRIORS["uniform"])
    first = torch.as_tensor(FIRST)
    last = torch.as_tensor(LAST)
    payoff = last @ torch.as_tensor(values) - torch.as_tensor(SEND_COST)
    fee = torch.as_tensor(SEND_COST)
    query_fee = torch.as_tensor(QUERY_COST)
    shapes = ((8, 4), (8, 4), (8, 4), (8, 4, 4, 4))
    params = tuple(torch.nn.Parameter(.04 * torch.randn(shape, generator=rng, dtype=torch.float64))
                   for shape in shapes)
    chair_legal = CHAIR_LEGAL.copy()
    if independent:
        chair_legal[:, 1:] = False
    masks = tuple(torch.as_tensor(mask) for mask in (route.SEND, route.SEND, chair_legal, FINAL_LEGAL))
    opt = torch.optim.Adam(params, lr=.13)
    trace = []
    for _ in range(UPDATES):
        left, right, chair, reply = (p.masked_fill(~mask, -torch.inf).softmax(-1)
                                     for p, mask in zip(params, masks, strict=True))
        opening = torch.einsum("lr,la,rb,abm->rbm", prior, left, right, first)
        heard = (1 - LOSS) * chair + LOSS * torch.eye(4, dtype=torch.float64)[0]
        end = torch.einsum("rbm,mq,rbqc->mc", opening, heard, reply)
        cost = prior.sum(1) @ (left @ fee) + prior.sum(0) @ (right @ fee) + opening.sum((0, 1)) @ (chair @ query_fee)
        score = (end * payoff).sum() - cost
        opt.zero_grad()
        (-score).backward()
        trace.append({"net_above_public_baseline": float(score.detach()),
                      "gradient_norms": [float(p.grad.norm()) for p in params]})
        assert np.isfinite([trace[-1]["net_above_public_baseline"], *trace[-1]["gradient_norms"]]).all()
        opt.step()
    options = tuple(p.detach().masked_fill(~mask, -torch.inf).argmax(-1).numpy()
                    for p, mask in zip(params, masks, strict=True))
    return options, trace


def exact_independent(prior, terminal):
    # Fix the left send table. The right desk chooses its two sends
    # jointly in each local inventory. Stochastic tables have a
    # deterministic maximizer for this objective.
    legal = [np.flatnonzero(row) for row in route.SEND]
    left = np.asarray(list(product(*legal)))
    values = np.einsum("abm,mcn,n->abc", FIRST, LAST, terminal)
    values -= SEND_COST[:, None, None] + SEND_COST[None, :, None] + SEND_COST[None, None, :]
    delivered = np.einsum("plbc,lr->prbc", values[left], prior)
    allowed = route.SEND[:, :, None] & route.SEND[:, None, :]
    candidates = np.where(allowed, delivered, -np.inf).reshape(len(left), 8, 16)
    index = candidates.max(-1).sum(-1).argmax()
    b, c = np.divmod(candidates[index].argmax(-1), 4)
    reply = np.broadcast_to(c[:, None, None], (8, 4, 4))
    return left[index], b, np.zeros(8, dtype=int), reply


def scripts():
    query, send, _ = route.scripted()
    reply = np.zeros((8, 4, 4), dtype=int)
    for inv, b, heard in product(range(8), range(4), range(4)):
        use = [i for i in range(1, 4) if route.SEND[inv, i] and i != b]
        reply[inv, b, heard] = heard if heard and route.SEND[inv, heard] else (use[0] if use else 0)
    return send, send, query, reply


def centralized_ceiling(prior, terminal):
    # Frictionless last-stage coordination provides an upper bound.
    # It sees both inventories and the received mask, with three
    # physical sends from the same desks and no fee for its signal.
    third = LAST @ terminal - SEND_COST
    optimal = np.where(route.SEND[:, None, :], third[None, :, :], -np.inf).max(-1)
    by_pair = np.einsum("abm,rm->rab", FIRST, optimal)
    adjusted = by_pair - SEND_COST[:, None] - SEND_COST[None, :]
    allowed = route.SEND[:, None, :, None] & route.SEND[None, :, None, :]
    return float(np.sum(prior * np.where(allowed, adjusted, -np.inf).max((2, 3))))


def run():
    fitting, held = data()
    learned, traces = {}, {}
    for name, independent in (("learned_query", False), ("learned_independent", True)):
        learned[name], trace = train(fitting, independent)
        traces[name] = {"updates": len(trace), "trace": trace, "policy": [x.tolist() for x in learned[name]]}
    result = {}
    for name, row in held.items():
        points = np.asarray(row["guarded"])
        orders = archive.calibrated_orders(points)
        for prior_name in ("uniform", "correlated_duplicates"):
            prior = route.TEST_PRIORS[prior_name]
            terminal = points + (points == 70) * COMPLETE_BONUS
            independent = measure(exact_independent(prior, terminal), prior, points)
            upper = centralized_ceiling(prior, terminal)
            cells = []
            for order in orders:
                target = archive.unama.reordered(points, order)
                arms = {k: measure(policy, prior, target) for k, policy in {**learned, "scripted_query": scripts()}.items()}
                arms["query_erased"] = measure(learned["learned_query"], prior, target, True)
                arms["two_send_ablation"] = measure((*learned["learned_query"][:2], np.zeros(8, dtype=int),
                                                       np.zeros((8, 4, 4), dtype=int)), prior, target)
                assert max(x["net"] for x in [*arms.values(), independent]) <= upper + 1e-9
                assert arms["learned_independent"]["net"] <= independent["net"] + 1e-9
                assert arms["two_send_ablation"]["strict_complete"] == 0
                cells.append({"order": order, "arms": arms})
            mean = {key: {metric: sum(cell["arms"][key][metric] for cell in cells) / len(cells)
                          for metric in ("guarded_points", "strict_complete", "cost", "net")}
                    for key in cells[0]["arms"]}
            result.setdefault(name, {})[prior_name] = {"orders": cells, "means": mean,
                                                       "exact_independent": independent, "centralized_ceiling": upper}
    return {"scope": "Exact loss replay and two matched new policy-gradient fits. Two historical source archives "
                     "with full attainable records and two recent archives with incomplete writers are held out of fitting. "
                     "Simulation uses typed card IDs and previously scored outputs.",
            "loss": LOSS, "complete_bonus": COMPLETE_BONUS, "fitting": fitting, "held": held,
            "training": traces, "results": result,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in (Path(__file__), Path(route.__file__))}}


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(run(), indent=2, ensure_ascii=False))
