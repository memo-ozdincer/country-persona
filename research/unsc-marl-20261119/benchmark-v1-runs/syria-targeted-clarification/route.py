"""Learn a one-question router from synthetic worlds and replay the live branches."""
from ast import literal_eval
from itertools import product
import json
from pathlib import Path
import sys

import torch

import collect_clarification as collection
import admit

HERE, E = collection.HERE, collection.E
sys.path.insert(0, str(HERE.parent / "workshop-joint-action-fit"))
import environment

LEDGER = collection.reader.review.ledger
OPTIONS = tuple("ABCD")
QUESTION_COST = .04
ERASURE = .08
UPDATES = 96
ACTIONS = ("silence", "ask-first", "ask-second")
DIMS = (
    "intercept", "target_lacks_exclusions", "target_lacks_acceptances", "other_has_exclusions",
    "other_has_acceptances", "target_conflicts", "other_conflicts", "already_certified",
    "unresolved_fraction",
)


def full(owner, compatible):
    return {"id": "answer:" + owner, "role": owner,
            "accepts": sorted(compatible), "excludes": sorted(set(OPTIONS) - set(compatible))}


def readout(roles, messages):
    state = LEDGER.readout(OPTIONS, roles, messages)
    return {"decision": admit.exact(state), "state": state}


def query(roles, messages, index, allowed):
    if allowed is None:
        return readout(roles, messages)
    speaker = roles[index]
    return readout(roles, [r for r in messages if r["role"] != speaker] + [full(speaker, allowed)])


def features(roles, current):
    initial = readout(roles, current)
    conflict = {r["role"] for r in initial["state"].get("conflicts", [])}
    excludes = [{o for r in current if r["role"] == p for o in r.get("excludes", [])} for p in roles]
    accepts = [{o for r in current if r["role"] == p for o in r.get("accepts", [])} for p in roles]
    unresolved = initial["state"].get("unresolved_options", [])
    return [[1., not excludes[i], not accepts[i], bool(excludes[1-i]), bool(accepts[1-i]),
             roles[i] in conflict, roles[1-i] in conflict, initial["decision"] != "U", len(unresolved) / 4]
            for i in (0, 1)]


def reward(prediction, targets):
    if prediction == "U":
        return .15
    return 1. if prediction in targets else -1.


def train_examples():
    # The original synthetic roster provides private conditions without any UN
    # cases. Reconstruct each role's local menu from its own full-disclosure prompt.
    synthetic = environment.development()
    observations, returns = [], []
    for world in synthetic:
        payload = json.loads(world["chair"][0][1]["content"])
        note = payload["public_notes"]
        local = [literal_eval(text.split("My full requirement is ", 1)[1].split("}.", 1)[0] + "}") for text in note]
        menu = []
        for choice in payload["menu"]:
            option, text = choice.split(": ", 1)
            menu.append({"id": option, **dict(t.split(" is ", 1) for t in text.split("; "))})
        compatible = [environment.allowed(menu, card) for card in local]
        assert sorted(compatible[0] & compatible[1] or {"I"}) == world["gold"]
        roles = ["first", "second"]
        variants = []
        for role, truth in zip(roles, compatible, strict=True):
            declaration = full(role, truth)
            accepted, rejected = sorted(truth)[0], sorted(set(OPTIONS) - truth)[0]
            variants.append([
                None, declaration | {"accepts": []}, declaration, declaration | {"accepts": [accepted], "excludes": []},
                declaration | {"accepts": [rejected]},
            ])
        for pair in product(*variants):
            messages = [m for m in pair if m is not None]
            obs = features(roles, messages)
            baseline = reward(readout(roles, messages)["decision"], world["gold"])
            change = [reward(query(roles, messages, i, truth)["decision"], world["gold"])
                      for i, truth in enumerate(compatible)]
            observations.append(obs)
            returns.append([baseline, *[(1-ERASURE)*score + ERASURE*baseline - QUESTION_COST for score in change]])
    return observations, returns


def probabilities(options, weights):
    routed = options @ weights
    silence = torch.zeros_like(routed[..., :1])
    return torch.cat((silence, routed), dim=-1).softmax(-1)


def train():
    torch.set_num_threads(1)
    examples, utility = train_examples()
    assert len(examples) == 400
    X = torch.tensor(examples, dtype=torch.float64)
    Y = torch.tensor(utility, dtype=torch.float64)
    w = torch.nn.Parameter(torch.zeros(len(DIMS), dtype=torch.float64))
    optimizer = torch.optim.Adam([w], lr=.14)
    trace = []
    for step in range(UPDATES + 1):
        mass = probabilities(X, w)
        expected = (mass * Y).sum(-1).mean()
        trace.append({"step": step, "utility": float(expected.detach()), "costed_query_rate": float((1-mass[:, 0]).mean().detach())})
        if step == UPDATES:
            break
        optimizer.zero_grad()
        (-expected + .001 * w.square().mean()).backward()
        assert torch.isfinite(w.grad).all()
        optimizer.step()
    realized = Y.gather(-1, probabilities(X, w).argmax(-1, keepdim=True))
    return {"weights": w.detach().tolist(), "trace": trace, "worlds": len(examples),
            "greedy_mean_utility": float(realized.mean()), "silence_mean_utility": float(Y[:, 0].mean())}


def parse(response):
    if response["termination"] != "complete":
        return None
    def unique_object(pairs):
        fields = dict(pairs)
        if len(fields) != len(pairs):
            raise ValueError("Duplicate response field")
        return fields

    try:
        out = json.loads(response["text"], object_pairs_hook=unique_object)
    except ValueError:
        return None
    if not isinstance(out, dict) or out.keys() != {"field", "value"}:
        return None
    field, value = out["field"], out["value"]
    if not isinstance(field, str) or not isinstance(value, str) or value not in collection.FIELDS.get(field, ()):
        return None
    return {field: value}


def missing_rule(roles, messages):
    initial = readout(roles, messages)
    if initial["decision"] != "U":
        return 0
    suspects = {c["role"] for c in initial["state"].get("conflicts", [])}
    if len(suspects) == 1:
        return roles.index(next(iter(suspects))) + 1
    missing = [i for i, role in enumerate(roles)
               if not any(m["role"] == role and m.get("excludes") for m in messages)]
    return missing[0] + 1 if missing else 0


def evaluate(model):
    routes = E.read(HERE.parent / "syria-public-evidence/recovery.json")["episodes"]
    responses = {r["id"]: r["response"] for r in map(
        json.loads, (HERE / "evidence/responses.jsonl").read_text().splitlines())}
    assert list(responses) == [r["id"] for r in collection.requests()]
    records = {}
    for key, case, notes in collection.reader.pair_inputs():
        comparison = routes[key]["scan_clause"]
        roles = [speaker for speaker, _ in notes]
        before = admit.messages(comparison["claims"], notes, case["options"])
        truth = dict(zip(case["roles"], case["membership"], strict=True))
        targets = ["I" if p == "IMPASSE" else p for p in case["gold"]]
        base = readout(roles, before)
        assert base["decision"] == comparison["decision"]
        corrections, outcomes = [], [base]
        for turn, role in enumerate(roles):
            declared = parse(responses[f"{key}/ask-{turn}"])
            valid = environment.allowed(case["options"], declared) if declared is not None else None
            outcomes.append(query(roles, before, turn, valid))
            corrections.append({"speaker": role, "declared": declared, "truth": declared == truth[role],
                                "compatible_packages": sorted(valid) if valid is not None else None})
        X = torch.tensor(features(roles, before), dtype=torch.float64)
        p = probabilities(X, torch.tensor(model["weights"], dtype=torch.float64))
        rules = {"silence": 0, "fixed_first": 1, "fixed_second": 2,
                 "ask_missing": missing_rule(roles, before), "learned": int(p.argmax())}
        records[key] = {"branch_outcomes": dict(zip(ACTIONS, outcomes, strict=True)), "clarifications": corrections,
                        "target": targets, "public_features": X.tolist(), "learned_probabilities": p.tolist(),
                        "policies": {name: {"action": ACTIONS[i], "asked": i != 0, "decision": outcomes[i]["decision"],
                                "correct": outcomes[i]["decision"] in targets,
                                "utility": reward(outcomes[i]["decision"], targets) - QUESTION_COST * (i != 0)}
                            for name, i in rules.items()}}
    scores = {name: {"queries": sum(r["policies"][name]["asked"] for r in records.values()),
                     "correct": sum(r["policies"][name]["correct"] for r in records.values()),
                     "wrong_commitments": sum(r["policies"][name]["decision"] != "U" and not r["policies"][name]["correct"]
                                              for r in records.values()),
                     "net_utility": sum(r["policies"][name]["utility"] for r in records.values())}
              for name in next(iter(records.values()))["policies"]}
    return {"records": records, "scores": scores,
            "truthful_clarifications": sum(a["truth"] for row in records.values() for a in row["clarifications"]),
            "correct_one_question_ceiling": sum(
                any(x["decision"] in r["target"] for x in r["branch_outcomes"].values()) for r in records.values())}


def run():
    model = train()
    return {"training": model, "features": DIMS, "question_cost": QUESTION_COST, "assumed_erasure_train": ERASURE,
            "evaluation": evaluate(model)}


if __name__ == "__main__":
    E.emit(run())
