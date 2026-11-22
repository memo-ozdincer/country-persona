"""Fit a one-query chair and a language-conditioned send decision together."""
from collections import defaultdict
import json
from pathlib import Path
import sys

import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import fit as reply_fit
import cases
import local_guard

assert reply_fit.HERE == HERE.parent
E = cases.E
QUERY_COST = .06
SEND_COST = cases.COST
TRAIN_RATES = ((.32, .83), (.83, .32), (.51, .69), (.69, .51))
HELD_RATES = ((.19, .97), (.97, .19), (.57, .88), (.88, .57))
UPDATES = 96
DTYPE = reply_fit.DTYPE
FEATURES = ("constant", "last_unknown", "certified", "public_similarity", "delivery", "similarity_delivery",
            "last_unknown_delivery")


def index(rows):
    groups = defaultdict(list)
    for i, row in enumerate(rows):
        key = row["id"].rsplit("/", 1)[0] if row["mode"] == "two_openings" else row["id"]
        groups[key].append((i, row))
    return list(groups.items())


def shared_public(group, as_held):
    first = group[0][1]
    packet = json.loads(first["messages"][1]["content"])
    common = {k: packet[k] for k in ("possible_packages", "public_claims")}
    for _, row in group[1:]:
        parsed = json.loads(row["messages"][1]["content"])
        assert all(parsed[k] == val for k, val in common.items())
    if first["mode"] != "two_openings":
        return 0.
    assert len(group) == 2
    if as_held:
        row = E.cases()[first["id"].split("/")[0]]
        attributes = {a["id"]: {k: v for k, v in a.items() if k not in {"id", "text"}} for a in row["options"]}
    else:
        attributes = {a["package"]: dict(x.split(" is ", 1) for x in a["proposal"].split("; "))
                      for a in common["possible_packages"]}
    left, right = [attributes[r["target"]] for _, r in group]
    assert set(left) == set(right)
    return sum(left[k] == right[k] for k in left) / len(left)


def feature(mode, similarity, rate):
    last = mode == "last_unknown"
    return [1., last, mode == "certified", similarity, rate, similarity*rate, last*rate]


def replay_rows(rows, as_held):
    if as_held:
        for row in rows:
            assert (local_guard.signature(row) == "Y") == row["truth"]
    roster = []
    for key, group in index(rows):
        mode = group[0][1]["mode"]
        if mode == "two_openings":
            assert len(group) == 2 and {row["role"] for _, row in group} == {0, 1}
        else:
            assert len(group) == 1
        similarity = shared_public(group, as_held)
        mapping = {row["role"]: (i, row) for i, row in group}
        for rates in HELD_RATES if as_held else TRAIN_RATES:
            row = {"key": key, "family": group[0][1]["family"], "mode": mode,
                   "similarity": similarity, "rates": rates, "offers": {}}
            for role, (i, presentation) in mapping.items():
                checked_action = "Y" if presentation["truth"] else "N"
                trace = presentation["audit"][checked_action]
                assert trace["truthful"] and not trace["wrong_commit"]
                row["offers"][role] = {"feature": feature(mode, similarity, rates[role]),
                                      "index": i, "sign_if_sent": checked_action,
                                      "disposition_if_delivered": trace["decision"], "helps": trace["new_proof"]}
            roster.append(row)
    return roster


def prepare(rows, representations, base_score):
    size = len(rows)
    eligible = torch.zeros((size, 2), dtype=torch.bool)
    chair_inputs = torch.zeros((size, 2, len(FEATURES)), dtype=DTYPE)
    sender_inputs = torch.zeros((size, 2, representations.shape[-1]), dtype=DTYPE)
    frozen_sender = torch.zeros((size, 2), dtype=DTYPE)
    delta = torch.zeros((size, 2), dtype=DTYPE)
    base = torch.tensor([1. if r["mode"] == "certified" else .15 for r in rows], dtype=DTYPE)
    for i, row in enumerate(rows):
        for role, claim in row["offers"].items():
            index = claim["index"]
            eligible[i, role] = True
            chair_inputs[i, role] = torch.tensor(claim["feature"], dtype=DTYPE)
            sender_inputs[i, role] = representations[index]
            frozen_sender[i, role] = torch.logsumexp(base_score[index, :2], dim=0) - base_score[index, 2]
            delta[i, role] = .85 * row["rates"][role] * claim["helps"] - SEND_COST
    return eligible, chair_inputs, sender_inputs, frozen_sender, delta, base


def actors(data, chair, sender):
    legal, x, h, logit, _, _ = data
    query = (x @ chair).masked_fill(~legal, -torch.inf)
    policy = torch.cat((torch.zeros_like(query[:, :1]), query), 1).softmax(-1)
    return policy, (logit + h @ sender).sigmoid()


def expected(p, s, data):
    _, _, _, _, delta, base = data
    return base + (p[:, 1:] * (s*delta - QUERY_COST)).sum(-1)


def train(data):
    _, x, h, _, _, _ = data
    c = torch.nn.Parameter(torch.zeros(x.shape[-1], dtype=DTYPE))
    r = torch.nn.Parameter(torch.zeros(h.shape[-1], dtype=DTYPE))
    opt = torch.optim.Adam((c, r), lr=.12)
    steps = []
    for step in range(UPDATES+1):
        values = expected(*actors(data, c, r), data).mean()
        steps.append({"step": step, "expected_team_return": float(values.detach())})
        if step == UPDATES:
            break
        opt.zero_grad()
        penalty = .002 * ((h @ r).square().mean() + c.square().mean())
        (-values + penalty).backward()
        assert all(torch.isfinite(weight.grad).all() for weight in (c, r))
        opt.step()
    return (c.detach(), r.detach()), steps


def prior_map(train_rows):
    distribution = defaultdict(list)
    # Rates repeat each view uniformly and therefore cancel in the estimated proportion.
    for row in train_rows:
        for claim in row["offers"].values():
            distribution[(row["mode"], row["similarity"])].append(int(claim["helps"]))
    return {key: sum(values)/len(values) for key, values in distribution.items()}


def evaluate(rows, data, weights, priors):
    legal, _, _, logit, delta, base = data
    selected, responders = actors(data, *weights)
    result = []
    for i, row in enumerate(rows):
        candidates = tuple(row["offers"])
        reliance = priors[(row["mode"], row["similarity"])]
        gain = {role: reliance*(.85*row["rates"][role]-SEND_COST) - QUERY_COST for role in candidates}
        best_prior = max(candidates, key=gain.__getitem__)
        choose_prior = best_prior + 1 if gain[best_prior] > 0. else 0
        terminal = row["mode"] == "certified"
        choose_first = 0 if terminal else min(candidates) + 1
        choose_delivery = 0 if terminal else max(candidates, key=row["rates"].__getitem__) + 1
        best_delta = {role: max(0., float(delta[i,role])) - QUERY_COST for role in candidates}
        peak = max(candidates, key=best_delta.__getitem__)
        ceiling = peak + 1 if best_delta[peak] > 0. else 0
        exact_send = delta[i].gt(0)
        fitted_send = responders[i].gt(.5)
        frozen_send = logit[i].gt(0)
        fitted_query = int(selected[i].argmax())
        systems = {
            "silence": (0, exact_send),
            "fixed_first_exact_reply": (choose_first, exact_send),
            "delivery_exact_reply": (choose_delivery, exact_send),
            "public_value_exact_reply": (choose_prior, exact_send),
            "public_value_frozen_reply": (choose_prior, frozen_send),
            "public_value_fitted_reply": (choose_prior, fitted_send),
            "learned_team": (fitted_query, fitted_send),
            "learned_chair_exact_reply": (fitted_query, exact_send),
            "learned_chair_frozen_reply": (fitted_query, frozen_send),
            "private_world_ceiling": (ceiling, exact_send),
        }
        arms = {}
        for name, (a, send) in systems.items():
            if a:
                role = a-1
                assert legal[i,role]
                issued = bool(send[role])
                claim = row["offers"][role]
                correct = issued and claim["helps"]
                arms[name] = {"choice": a, "sent": issued, "useless": issued and not correct,
                              "new_disposition_if_delivered": claim["disposition_if_delivered"] if correct else None,
                              "completion_probability": row["rates"][role] if correct else 0.,
                              "net": float(base[i]) + (float(delta[i,role]) if issued else 0.) - QUERY_COST}
            else:
                arms[name] = {"choice": 0, "sent": False, "useless": False, "new_disposition_if_delivered": None,
                              "completion_probability": 0., "net": float(base[i])}
        assert all(a["net"] <= arms["private_world_ceiling"]["net"] + 1e-10 for a in arms.values())
        result.append({k:v for k,v in row.items() if k != "offers"} | {"public_rate": reliance, "arms": arms})
    return result


def summary(rows):
    groups = sorted({r["mode"] for r in rows}) + sorted({r["family"] for r in rows})
    out = {}
    for subset in ("all", *groups):
        group = [x for x in rows if subset in {"all", x["family"], x["mode"]}]
        names = group[0]["arms"].keys()
        out[subset] = {}
        for name in names:
            scores = [r["arms"][name] for r in group]
            out[subset][name] = {"n": len(scores), "net": sum(a["net"] for a in scores)/len(scores),
                                 "queries": sum(a["choice"] != 0 for a in scores),
                                 "sent": sum(a["sent"] for a in scores),
                                 "useless": sum(a["useless"] for a in scores),
                                 "expected_new_proofs": sum(a["completion_probability"] for a in scores)}
    return out


def run():
    torch.set_num_threads(1)
    roster, hidden, base, _ = reply_fit.observations()
    n = len(roster["train"])
    train_rows = replay_rows(roster["train"], False)
    held_rows = replay_rows(roster["held"], True)
    train_data = prepare(train_rows, hidden[:n], base[:n])
    held_data = prepare(held_rows, hidden[n:], base[n:])
    weights, steps = train(train_data)
    priors = prior_map(train_rows)
    observed = evaluate(held_rows, held_data, weights, priors)
    return {"features": FEATURES, "updates": UPDATES, "train_presentation_count": len(train_rows),
            "trace": steps, "weights": [w.tolist() for w in weights], "held": observed, "summary": summary(observed),
            "public_calibration": {f"{k[0]}/{k[1]}": v for k,v in sorted(priors.items())},
            "sha256": {p.name: reply_fit.digest(p) for p in (Path(__file__), HERE / "protocol.md",
                HERE.parent / "roster.json", HERE.parent / "evidence/vectors.npz")}}


if __name__ == "__main__":
    E.emit(run())
