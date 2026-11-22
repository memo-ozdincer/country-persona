"""Check public policy selection and the source-value approximation."""
from itertools import product
from hashlib import sha256
import json
from pathlib import Path

import numpy as np

import source_aware as fit

HERE = Path(__file__).resolve().parent
s, g = fit.score, fit.game
SHIFTS = (
    ((.9, .9, .9), (.9, .8, .35)),
    ((.9, .9, .9), (.45, .45, .45)),
    ((.9, .8, .35), (.35, .8, .35)),
)


def measure(menu, evaluate, rates, cap, team):
    doc, correct, strict, asks, sends = map(float, np.mean([
        s.expected(menu, evaluate, rates, world, cap, *team) for world in g.WORLDS], axis=0))
    return {"points": doc * 70, "accuracy": correct, "strict": strict,
            "net": doc - fit.core.QUERY_COST * asks - fit.core.SEND_COST * sends,
            "questions": asks, "attempts": sends}


def compare(menu, evaluate, packet_values, heads, belief, actual, cap):
    former = s.arms_for(menu, belief)
    actors = {"former": former["learned"], "aware": fit.deploy(menu, belief, packet_values, heads),
              "silent": former["silent"]}
    forecast = {name: measure(menu, evaluate, belief, cap, pair) for name, pair in actors.items()}
    # Prefer silence on a net tie so an unproductive query cannot win by ordering.
    selected = max(actors, key=lambda name: (forecast[name]["net"], name == "silent"))
    observed = {name: measure(menu, evaluate, actual, cap, pair) for name, pair in actors.items()}
    hindsight = max(row["net"] for row in observed.values())
    return {"selected": selected, "predicted_net": forecast[selected]["net"],
            "observed": observed, "selected_net": observed[selected]["net"],
            "regret_to_hindsight_candidate": hindsight - observed[selected]["net"]}


def verify_values(evaluate, menu, values):
    states_checked = 0
    for state in product((-1, 0, 1), repeat=3):
        decision = g.terminal(menu, state)[0]
        compatible = [world for world in g.WORLDS
                      if all(bit == -1 or bit == actual for bit, actual in zip(state, world, strict=True))]
        expected = fit.value(np.array([menu]), np.array([state]), np.array([values]))[0]
        for world in compatible:
            gold = g.terminal(menu, world)[0]
            assert abs(evaluate(state, gold)[0] - expected) < 1e-10
            assert decision in ("UNRESOLVED", gold)
            states_checked += 1
    return states_checked


def run():
    outcome = s.e.read(HERE / "results.json")
    heads = {int(h): tuple(tuple(np.array(x) for x in a) for a in pair) for h, pair in outcome["heads"].items()}
    regenerated = fit.compare(heads)
    assert json.loads(json.dumps(regenerated)) == outcome["evaluation"]
    native = {row["arm"]: s.r.parse(row["reply"]) for row in s.review.rows("calls.jsonl")}
    matched, shifts, verified = {}, {}, {}
    for arm in s.r.ARMS:
        context = s.r.load(arm)
        menu = context[1]
        evaluate = s.documentary(arm, native[arm], context)
        values = tuple(outcome["evaluation"][arm]["packet_values"])
        verified[arm] = verify_values(evaluate, menu, values)
        matched[arm], shifts[arm] = {}, {}
        for rates, cap in product(g.HELD, (2, 3)):
            row = compare(menu, evaluate, values, heads, rates, rates, cap)
            assert row["regret_to_hindsight_candidate"] < 1e-10
            exact = outcome["evaluation"][arm]["conditions"][f"{rates}/{cap}"]["exact_net"]
            matched[arm][f"{rates}/{cap}"] = row | {"exact_net": exact}
        for (belief, actual), cap in product(SHIFTS, (2, 3)):
            shifts[arm][f"{belief}->{actual}/{cap}"] = compare(menu, evaluate, values, heads, belief, actual, cap)
    pins = (Path(__file__), HERE / "chooser-protocol.md", HERE / "results.json", Path(fit.__file__))
    return {"world_state_score_crosschecks": verified, "matched": matched, "delivery_shift": shifts,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in pins}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
