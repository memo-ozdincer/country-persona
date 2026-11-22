"""Train a receipt-aware chair and responder on public rubric and opening-plan features."""
import argparse
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path

import numpy as np

import facilitator_third_delivery_attribution as diagnose
import source_request_policy as route

delivery = diagnose.delivery
HERE = Path(__file__).resolve().parent
THIS_EVIDENCE = HERE / "facilitator-third-delivery-evidence"
RECEIPTS = np.arange(8)
SLOTS = tuple(combinations(range(3), 2))
UPDATES = 240


def rubric(public, singles, pair=None, bonus=0):
    return np.array([public + sum(w for i, w in enumerate(singles) if mask & (1 << i))
                     + (bonus if pair is not None and mask & pair == pair else 0) for mask in RECEIPTS])


def terminal(points):
    return points + (points == 70) * delivery.COMPLETE_BONUS


def cases():
    historical, held = delivery.data()
    fit = {}
    for name in ("outer_space", "mali", "climate"):
        observed = np.asarray(historical[name]["guarded"])
        if name == "outer_space":
            public = rubric(21, (7, 14, 7), 3, 14)
        elif name == "mali":
            public = rubric(56, (7, 7, 0))
        else:
            public = rubric(35, (7, 7, 7), 3, 7)
        fit[name] = (public, observed)
    # Change which two sources are complementary at fixed singleton weights.
    # These authored profiles have three materially required sources at most.
    for weights in ((6, 9, 11), (5, 8, 13), (9, 9, 8)):
        for pair in SLOTS:
            mask = sum(1 << i for i in pair)
            for strength in (4, 10, 16):
                public = rubric(70 - sum(weights) - strength, weights, mask, strength)
                fit[f"{weights}/{mask}/{strength}"] = (public, public)
    declared = {
        "unifil": rubric(35, (7, 7, 7), 3, 14),
        "myanmar": rubric(42, (7, 7, 7), 3, 7),
        "unama": rubric(34, (12, 12, 12)),
        "emergency": rubric(34, (12, 12, 12)),
    }
    evaluation = {name: (declared[name], np.asarray(row["guarded"])) for name, row in held.items()}
    assert not (fit.keys() & evaluation.keys())
    assert not {tuple(x[0]) for x in fit.values()} & {tuple(x[0]) for x in evaluation.values()}
    return fit, evaluation


def context(public, prior):
    left, right, _, _ = delivery.exact_independent(prior, terminal(public))
    opening = np.einsum("lr,la,rb,abm->rbm", prior, delivery.one_hot(left), delivery.one_hot(right), delivery.FIRST)
    n = terminal(public)
    # Identical declared information for request and reply. The output tables
    # restrict their episode-time information independently.
    features = np.concatenate(((n - n[0]) / 36., delivery.one_hot(left).ravel(),
                               delivery.one_hot(right).ravel(), prior.ravel() * 8))
    return left, right, opening, features


def train(fitting):
    import torch

    torch.set_num_threads(1)
    torch.manual_seed(route.SEED)
    prior = route.TEST_PRIORS["uniform"]
    contexts = [context(public, prior) for public, _ in fitting.values()]
    inputs = torch.as_tensor(np.stack([row[-1] for row in contexts]), dtype=torch.float32)
    opening = torch.as_tensor(np.stack([row[2] for row in contexts]), dtype=torch.float32)
    values = [terminal(actual) - actual[0] for _, actual in fitting.values()]
    payoff = torch.as_tensor(np.einsum("mcn,pn->pmc", delivery.LAST, values) - delivery.SEND_COST,
                             dtype=torch.float32)
    c_feasible = torch.as_tensor(delivery.CHAIR_LEGAL)
    r_feasible = torch.as_tensor(delivery.FINAL_LEGAL)
    signal_fee = torch.as_tensor(delivery.QUERY_COST, dtype=torch.float32)
    silence = torch.eye(4)[0]
    net = torch.nn.Sequential(torch.nn.Linear(inputs.shape[1], 48), torch.nn.Tanh(),
                              torch.nn.Linear(48, 48), torch.nn.Tanh(), torch.nn.Linear(48, 544))
    opt = torch.optim.Adam(net.parameters(), lr=.012)
    trace = []
    for _ in range(UPDATES):
        q, r = net(inputs).split((32, 512), dim=-1)
        chair = q.reshape(-1, 8, 4).masked_fill(~c_feasible, -torch.inf).softmax(-1)
        reply = r.reshape(-1, 8, 4, 4, 4).masked_fill(~r_feasible, -torch.inf).softmax(-1)
        heard = (1 - delivery.LOSS) * chair + delivery.LOSS * silence
        dispatch = torch.einsum("prbm,pmq,prbqc->pmc", opening, heard, reply)
        fees = torch.einsum("prbm,pmq,q->p", opening, chair, signal_fee)
        expected = torch.einsum("pmc,pmc->p", dispatch, payoff) - fees
        objective = expected.mean()
        assert torch.isfinite(objective)
        opt.zero_grad()
        (-objective).backward()
        trace.append(float(objective.detach()))
        opt.step()
    return net.eval(), trace


def tail(network, features, opening):
    import torch

    with torch.inference_mode():
        output = network(torch.as_tensor(features, dtype=torch.float32)).numpy()
    chair = np.where(delivery.CHAIR_LEGAL, output[:32].reshape(8, 4), -np.inf).argmax(-1)
    reply = np.where(delivery.FINAL_LEGAL, output[32:].reshape(8, 4, 4, 4), -np.inf).argmax(-1)
    return *opening, chair, reply


def evaluate(network, evaluation, old):
    report = {}
    for name, (public, actual) in evaluation.items():
        report[name] = {"public_rubric_points": public.tolist(), "scored_record_points": actual.tolist(),
                        "priors": {}}
        for prior_label in ("uniform", "correlated_duplicates"):
            prior = route.TEST_PRIORS[prior_label]
            left, right, _, features = context(public, prior)
            exact_public = delivery.exact_independent(prior, terminal(public))
            public_tail, _ = diagnose.exact_tail(left, right, prior, terminal(public))
            hindsight_tail, _ = diagnose.exact_tail(left, right, prior, terminal(actual))
            trained = tail(network, features, (left, right))
            constant = features.copy()
            constant[:8] = (terminal(rubric(34, (12, 12, 12))) - 34) / 36.
            ablated = tail(network, constant, (left, right))
            _, _, c, r = delivery.scripts()
            plans = {"learned": trained, "constant_rubric": ablated, "scripted_tail": (left, right, c, r),
                     "public_independent": exact_public, "public_exact_tail": public_tail,
                     "hindsight_exact_tail": hindsight_tail}
            for plan in plans.values():
                diagnose.audit(plan, prior)
            scores = {key: delivery.measure(plan, prior, actual) for key, plan in plans.items()}
            scores["learned_erased"] = delivery.measure(trained, prior, actual, erase=True)
            assert max(row["net"] for row in scores.values()) <= scores["hindsight_exact_tail"]["net"] + 1e-9
            scores["previous_learned"] = old["results"][name][prior_label]["means"]["learned_query"]
            report[name]["priors"][prior_label] = {"arms": scores,
                                                 "learned_policy": [a.tolist() for a in trained]}
    return report


def run():
    fitting, evaluation = cases()
    before = THIS_EVIDENCE / "fit.json"
    prepared = json.loads(before.read_text())
    net, trace = train(fitting)
    return {
        "scope": "Joint exact expected-reward fit of chair and responder. Their opening is fixed by the same "
                 "public-rubric independent plan for all matched controls. Held-out historical outcomes enter scoring only. "
                 "Hindsight tail sees the exact assessment bank.",
        "updates": len(trace), "training_trace": trace,
        "fit": {name: {"public": p.tolist(), "observed": r.tolist()} for name, (p, r) in fitting.items()},
        "network": {key: value.tolist() for key, value in net.state_dict().items()},
        "transfer": evaluate(net, evaluation, prepared),
        "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in (
            Path(__file__), Path(delivery.__file__), Path(diagnose.__file__), before)},
    }


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(run(), indent=2, ensure_ascii=False))
