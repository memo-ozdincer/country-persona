"""Joint routing and truthful reply policies with a single signed answer."""
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import sys

import torch

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
sys.path.insert(0, str(PROJECT / "benchmark-v1"))
sys.path.insert(0, str(PROJECT / "crossbench"))
import evaluate as benchmark
import decision_ledger as ledger

DTYPE = torch.float64
UPDATES = 96
QUERY_COST = .06
SEND_COST = .035
ROLES = ("first", "second")
TRAIN_SUPPORT = (.18, .58, .86)
TRAIN_DELIVERY = (.28, .60, .92)
HELD_SUPPORT = (.09, .42, .73, .95)
HELD_DELIVERY = (.18, .49, .79, .96)
MODES = ("two_openings", "last_unknown", "certified")
LABELS = ("quiet", "ask_first", "ask_second")


def message(i, label, accepted, key):
    return {"id": key, "role": ROLES[i], "accepts": [label] if accepted else [],
            "excludes": [] if accepted else [label]}


def readout(labels, messages):
    row = ledger.readout(labels, ROLES, messages)
    if row["state"] == "AGREEMENT_POSSIBLE":
        return sorted(row["verified_options"])[0]
    return "I" if row["state"] == "IMPASSE" else "U"


def material(action, hidden):
    if action == "U":
        return .15
    valid = hidden[0] & hidden[1] or {"I"}
    assert action in valid
    return 1.


def setup(labels, mode, order):
    a, b, *_ = labels
    if mode == "two_openings":
        return (message(0, a, True, "opening-0"), message(1, b, True, "opening-1")), (b, a)
    known = order
    openings = [message(known, a, True, "known")]
    openings.extend(message(known, option, False, f"excluded-{option}") for option in labels[1:])
    if mode == "certified":
        openings.append(message(1 - known, a, True, "known-peer"))
    return tuple(openings), (a, a)


def hidden_sets(labels, openings, targets, signs):
    reachable = []
    for i, sign in enumerate(signs):
        compatible = {label for item in openings if item["role"] == ROLES[i] for label in item["accepts"]}
        rejected = {label for item in openings if item["role"] == ROLES[i] for label in item["excludes"]}
        bit = targets[i]
        if sign and bit not in rejected:
            compatible.add(bit)
        if not compatible:
            allowed = [p for p in labels if p not in rejected and p != bit]
            compatible.add(allowed[0])
        reachable.append(compatible)
    return reachable


def before_signs(openings, targets, p):
    for i, label in enumerate(targets):
        facts = [row for row in openings if row["role"] == ROLES[i]]
        if any(label in row["accepts"] for row in facts):
            yield (0., 1.)
        elif any(label in row["excludes"] for row in facts):
            yield (1., 0.)
        else:
            yield (1. - p[i], p[i])


def build(labels, mode, order, p, q, family):
    labels = labels[order:] + labels[:order]
    openings, targets = setup(labels, mode, order)
    initial = readout(labels, openings)
    sign_mass = tuple(before_signs(openings, targets, p))
    chair_x, reply_x, reply_outcomes = [], [], []
    for i in range(2):
        peer_accepts = any(row["role"] != ROLES[i] and targets[i] in row["accepts"] for row in openings)
        already = any(row["role"] == ROLES[i] and targets[i] in row["accepts"] for row in openings)
        remaining = set(labels) - {x for row in openings for x in row["excludes"]}
        sign_cases = []
        recipient_inputs = []
        for sign in (False, True):
            row = message(i, targets[i], sign, "reply")
            sign_cases.append(readout(labels, [*openings, row]) if sign_mass[i][int(sign)] else initial)
            recipient_inputs.append([1., sign, peer_accepts, already, len(remaining)/len(labels),
                                     bool(sign and peer_accepts), bool(not sign and len(remaining)==1),
                                     initial != "U", q[i]])
        possible = any(a != "U" and a != initial for a in sign_cases)
        chair_x.append([1., p[i], q[i], p[i] * q[i], possible, already, peer_accepts,
                        len(remaining)/len(labels), initial != "U", bool(remaining == {targets[i]})])
        reply_x.append(recipient_inputs)
        reply_outcomes.append(sign_cases)
    base = .15 if initial == "U" else 1.
    # Check every reachable hidden pair, including the sign fixing any potential proof.
    class_weights = [[0., 0.] for _ in range(2)]
    events = []
    for signs in product((False, True), repeat=2):
        mass = sign_mass[0][int(signs[0])] * sign_mass[1][int(signs[1])]
        if not mass:
            continue
        hidden = hidden_sets(labels, openings, targets, signs)
        assert all(ledger.truthful_disclosure(row, hidden[ROLES.index(row["role"])]) for row in openings)
        material(initial, hidden)
        after = [reply_outcomes[i][int(signs[i])] for i in (0, 1)]
        for action in after:
            material(action, hidden)
        events.append({"signs": signs, "weight": mass, "class": "agreement" if hidden[0] & hidden[1] else "impasse",
                       "live_dispositions": after, "true_compatible": [sorted(v) for v in hidden]})
        for i in (0, 1):
            class_weights[i][int(signs[i])] += mass
    assert abs(sum(x["weight"] for x in events) - 1) < 1e-12
    ask_u = [[q[i] * ((1. if a != "U" else .15) - base) - SEND_COST
              for a in reply_outcomes[i]] for i in (0, 1)]
    possible = [any(a != initial and a != "U" for a in reply_outcomes[i]) for i in (0, 1)]
    return {"family": family, "labels": labels, "mode": mode, "order": order, "prior": p, "delivery": q, "initial": initial,
            "openings": openings, "targets": targets, "features": chair_x, "recipient": reply_x,
            "base": base, "sign_mass": class_weights, "send_deltas": ask_u, "proof_possible": possible,
            "events": events}


def roster():
    train = [build(tuple("ABCD"), mode, order, p, q, "synthetic") for mode, order, p, q in product(
        MODES, (0, 1), product(TRAIN_SUPPORT, repeat=2), product(TRAIN_DELIVERY, repeat=2))]
    cases = benchmark.cases()
    families = {v["family"]: tuple(o["id"] for o in v["options"]) for v in cases.values() if v["track"] == "workshop"}
    test = [build(labels, mode, order, p, q, family) for (family, labels), mode, order, p, q in product(
        families.items(), MODES, (0, 1), product(HELD_SUPPORT, repeat=2), product(HELD_DELIVERY, repeat=2))]
    return train, test


def tensors(rows):
    get = lambda key: torch.tensor([row[key] for row in rows], dtype=DTYPE)
    return tuple(get(k) for k in ("features", "recipient", "sign_mass", "send_deltas", "base"))


def policies(x, y, cw, rw):
    logits = x @ cw
    chair = torch.cat((torch.zeros_like(logits[:, :1]), logits), 1).softmax(-1)
    send = (y @ rw).sigmoid()
    return chair, send


def weighted_team(p, s, sign, delta, base):
    return base + (p[:, 1:] * ((s * sign * delta).sum(-1) - QUERY_COST)).sum(-1)


def fit(rows):
    x, y, sign, delta, base = tensors(rows)
    cw, rw = [torch.nn.Parameter(torch.zeros(t.shape[-1], dtype=DTYPE)) for t in (x, y)]
    opt = torch.optim.Adam((cw, rw), lr=.12)
    trace = []
    for step in range(UPDATES + 1):
        p, s = policies(x, y, cw, rw)
        value = weighted_team(p, s, sign, delta, base).mean()
        trace.append({"step": step, "expected_team_utility": float(value.detach()),
                      "question_probability": float((1-p[:,0]).mean().detach())})
        if step == UPDATES:
            break
        opt.zero_grad()
        (-value + .001 * (cw.square().mean() + rw.square().mean())).backward()
        assert all(torch.isfinite(w.grad).all() for w in (cw, rw))
        opt.step()
    return cw.detach(), rw.detach(), trace


def select(row, priorities):
    if row["initial"] != "U" or not any(row["proof_possible"]):
        return 0
    return 1 + max((i for i, ok in enumerate(row["proof_possible"]) if ok),
                   key=lambda i: priorities[i])


def evaluate(rows, weights):
    x, y, sign, delta, base = tensors(rows)
    chair, sender = policies(x, y, *weights)
    best_reply = delta.gt(0)
    best_query_value = (sign * delta.clamp_min(0)).sum(-1) - QUERY_COST
    ceiling = torch.cat((torch.zeros_like(best_query_value[:, :1]), best_query_value), 1)
    results = []
    for i, r in enumerate(rows):
        learned = int(chair[i].argmax())
        exact = int(ceiling[i].argmax())
        ready_product = tuple(a*b for a,b in zip(r["prior"], r["delivery"], strict=True))
        variants = {
            "silence": (0, best_reply[i]),
            "fixed_first": (int(r["initial"] == "U"), best_reply[i]),
            "fixed_second": (2*int(r["initial"] == "U"), best_reply[i]),
            "proof_first": (select(r, (1., 0.)), best_reply[i]),
            "delivery_first": (select(r, r["delivery"]), best_reply[i]),
            "compatibility_first": (select(r, r["prior"]), best_reply[i]),
            "probability_product": (select(r, ready_product), best_reply[i]),
            "learned_team": (learned, sender[i].gt(.5)),
            "learned_chair_exact_reply": (learned, best_reply[i]),
            "exact_chair_learned_reply": (exact, sender[i].gt(.5)),
            "exact_public_oracle": (exact, best_reply[i]),
        }
        values = {}
        for name, (question, response) in variants.items():
            total = 0.
            certificates = Counter()
            speaker = question - 1
            for branch in r["events"]:
                q = r["delivery"][speaker] if question and response[speaker,int(branch["signs"][speaker])] else 0.
                after = branch["live_dispositions"][speaker] if q else r["initial"]
                score = q * (1. if after != "U" else .15) + (1.-q) * r["base"]
                sends = float(question and response[speaker,int(branch["signs"][speaker])])
                total += branch["weight"] * (score - QUERY_COST * bool(question) - SEND_COST * sends)
                certificates[branch["class"]] += branch["weight"] * (
                    q * (after != "U") + (1.-q) * (r["initial"] != "U"))
            values[name] = {"question": LABELS[question], "net": total,
                            "agreement_mass": certificates["agreement"], "impasse_mass": certificates["impasse"]}
        assert abs(values["exact_public_oracle"]["net"] - (r["base"] + float(ceiling[i].max()))) < 1e-10
        assert all(v["net"] <= values["exact_public_oracle"]["net"] + 1e-10 for v in values.values())
        results.append({"family": r["family"], "mode": r["mode"], "order": r["order"], "prior": r["prior"],
                        "delivery": r["delivery"], "arms": values})
    return results


def aggregate(results):
    totals = {}
    for kind in ("all", *MODES):
        rows = [r for r in results if kind == "all" or r["mode"] == kind]
        totals[kind] = {name: {"net": sum(r["arms"][name]["net"] for r in rows)/len(rows),
                               "question_rate": sum(r["arms"][name]["question"] != "quiet" for r in rows)/len(rows),
                               "agreement_mass": sum(r["arms"][name]["agreement_mass"] for r in rows)/len(rows),
                               "impasse_mass": sum(r["arms"][name]["impasse_mass"] for r in rows)/len(rows)}
                        for name in rows[0]["arms"]}
    return totals


def run():
    torch.set_num_threads(1)
    benchmark.cases()
    a, b = roster()
    cw, rw, trace = fit(a)
    dev = evaluate(a, (cw, rw))
    held = evaluate(b, (cw, rw))
    files = (Path(__file__), HERE / "protocol.md", benchmark.HERE / "release.json")
    return {"train_states": len(a), "held_states": len(b), "weights": [cw.tolist(), rw.tolist()],
            "trace": trace, "train": aggregate(dev), "test": aggregate(held), "test_states": held,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    benchmark.emit(run())
