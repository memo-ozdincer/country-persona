"""Locked documentary transfer of the receipt-conditioned selector."""
import argparse
from itertools import product
import json
from pathlib import Path
from statistics import mean
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "cooperative-rollout-fit/evidence-choice/receipt-conditioned"
sys.path.insert(0, str(PRIOR))
import private_receipt as private
import receipt_choice as learned

READ, old = learned.loss.old.tribunals.wire.n.read, learned.old
frozen = old.tribunals.frozen
CASE = READ(HERE / "docket.json")
COUNTS = (2, 2, 2)
CAPS = (1, 1, 1)
ORDERS = {"uk_later": (0, 1, 2), "germany_later": (1, 0, 2)}
SHARES = (.25, .50, .75)
RATES = learned.loss.RATES


def plan():
    files = (Path(__file__), HERE / "protocol.md", HERE / "docket.json",
             HERE / "provenance.json", HERE / "join_sources.py", PRIOR / "results.json",
             PRIOR / "receipt_choice.py", PRIOR / "private_receipt.py", old.tribunals.RELEASE / "release.json")
    return {"case": CASE["id"], "orders": {k: list(v) for k, v in ORDERS.items()},
            "rates": list(RATES), "private_first_card_probability": list(SHARES),
            "sha256": {str(file.relative_to(old.tribunals.STUDY)): old.DIGEST(file) for file in files}}


def render(card_ids):
    evidence = {r["id"]: r for r in frozen.evidence(CASE)}
    visible = {r["id"] for r in CASE["public"]} | set(card_ids)
    selected = [item for key, item in evidence.items() if key in visible]
    relations = [r for r in CASE["relations"] if set(r["needs"]) <= visible]
    spans = {item["id"]: (item["text"], (item["id"],)) for item in selected}
    spans.update({r["id"]: (r["text"], r["needs"]) for r in relations})
    answer = "\n".join([item["text"] for item in selected] + [r["text"] for r in relations])
    calls = [{}, {}, {"text": answer, "termination": "complete"}]
    packet = frozen.final_packet(CASE, calls)
    units = []
    for rule in CASE["rubric"]:
        key = rule["id"]
        span, needs = spans.get(key, ("", ()))
        units.append({"id": key, "status": "met" if span else "unmet", "response": span,
                      "source": [{"block": src, "quote": evidence[src]["text"]} for src in needs],
                      "reason": "The necessary sourced clause or clauses were delivered." if span else
                                "A necessary source clause is absent."})
    verdict = {"id": packet["id"], "units": units, "guard": {"status": "clear", "response": "",
               "source": [], "reason": "Every rendered clause is scoped to the identified archive evidence."}}
    result = frozen.final_score(CASE, calls, verdict)
    assert result["release"]
    return {"text": answer, "score": result, "marks": verdict}


def setup(order):
    menus = [CASE["owned"][i] for i in order]
    weights = {r["id"]: r["weight"] for r in CASE["rubric"]}
    positions = {card["id"]: (i, j) for i, menu in enumerate(menus) for j, card in enumerate(menu)}
    local = [np.asarray([weights[r["id"]] for r in menu]) for menu in menus]
    edges = []
    for relation in CASE["relations"]:
        (i, a), (j, b) = sorted(positions[key] for key in relation["needs"])
        edges.append((i, a, j, b, weights[relation["id"]]))
    rows = {}
    for action in product(range(2), repeat=3):
        rows[action] = [render([menus[i][choice]["id"] for i, choice in enumerate(action) if mask & 1 << i])
                        for mask in range(8)]
    true = {action: [row["score"]["released_70"] for row in states] for action, states in rows.items()}
    return menus, local, edges, rows, true


def direct_replay(scene, plan_, true):
    b, c, by_view = plan_
    return sum(prob * true[(by_view[b + 1 if mask & 2 else 0], b, c)][mask]
               for mask, prob in enumerate(scene["mask_probabilities"]))


def test_private(scene, local, edges, share, rate, fitted, true):
    # The early desk is forced to send its one private card. Its type may affect the uninformed third desk's forecast.
    shares = np.array((share, 1. - share))
    probabilities = shares[:, None] * scene["mask_probabilities"][None, :]
    by_content = scene["adaptive"]
    present = np.einsum("b,baf->af", shares, by_content[1:])
    observed = scene["observe"]
    third = scene["open"][2].copy()
    prior = old.softmax(local[1] / 3)
    for i, a, j, b, w in edges:
        if (i, j) == (1, 2):
            correction = shares[a] - np.array([.5, prior[a]])
            third[b, 1:] += w * rate * correction / 7
    modes = {"content": (observed, by_content),
             "arrival": ((observed > 0).astype(int), np.stack((by_content[0], present))),
             "none": (np.zeros_like(observed), ((1 - rate) * by_content[0] + rate * present)[None, :, :])}
    public = true[(0, 0, 0)][0]
    outcome = {}
    for mode, (view, design) in modes.items():
        exact, actions, last = private.optimal(scene["returns"], probabilities, view)
        collection = {"oracle": (actions, last)}
        for arm, weights in (("learned", fitted), ("fixed", np.array([1., 0., 1.]))):
            collection[arm] = (np.argmax(design @ weights, axis=1).tolist(), int(np.argmax(third @ weights)))
        performance = {}
        for arm, (action, last) in collection.items():
            value = private.expected(scene["returns"], probabilities, view, np.asarray(action), last) + public
            independent = sum(probabilities[b, mask] * true[(action[view[b, mask]], b, last)][mask]
                              for b, mask in product(range(2), range(8)))
            assert abs(independent - value) < 1e-9
            assert value <= exact + public + 1e-9
            performance[arm] = {"released": value, "by_view": action, "third": last}
        outcome[mode] = performance
    assert outcome["content"]["oracle"]["released"] >= outcome["arrival"]["oracle"]["released"] - 1e-9
    return outcome


def run():
    assert plan() == READ(HERE / "plan.json")
    fit = np.array(READ(PRIOR / "results.json")["training"][-1]["weights"])
    previous = np.array(READ(PRIOR.parent / "delivery-aware/results.json")["trace"][-1]["weights"])
    control = render([item["id"] for role in CASE["owned"] for item in role])
    assert control["score"]["released_70"] == 70
    output, exact_replays = {}, 0
    for label, order in ORDERS.items():
        menus, local, edges, rows, true = setup(order)
        reference = true[(0, 0, 0)][0]
        scores, held = [], []
        for rate in RATES:
            scene = learned.features(COUNTS, CAPS, local, edges, (rate,) * 3, true)
            points, policies = learned.compare(scene, fit, previous)
            released = {key: value + reference for key, value in points.items()}
            for arm, policy in policies.items():
                assert abs(released[arm] - direct_replay(scene, policy, true)) < 1e-9
            exact_replays += len(policies)
            scores.append({"receipt": rate, "released": released, "policies": policies})
            for share in SHARES:
                held.append({"receipt": rate, "first_card_probability": share,
                             "outcomes": test_private(scene, local, edges, share, rate, fit, true)})
                exact_replays += 9
        output[label] = {"roles": [CASE["roles"][i] for i in order], "public_inventory": scores,
                         "forced_private_inventory": held, "records": {''.join(map(str, a)): poses for a, poses in rows.items()},
                         "max_capacity_record": max(v[-1] for v in true.values()),
                         "mean_learned_over_fixed": mean(r["released"]["learned_adaptive"] -
                                                          r["released"]["fixed_receipt_priority"] for r in scores),
                         "mean_private_content_value": mean(r["outcomes"]["content"]["oracle"]["released"] -
                                                              r["outcomes"]["arrival"]["oracle"]["released"] for r in held)}
    return {"orders": output, "full_source_calibration": control, "independent_dispatch_checks": exact_replays,
            "plan_sha256": old.DIGEST(HERE / "plan.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run"))
    print(json.dumps({"plan": plan, "run": run}[parser.parse_args().mode](), ensure_ascii=False, indent=2))
