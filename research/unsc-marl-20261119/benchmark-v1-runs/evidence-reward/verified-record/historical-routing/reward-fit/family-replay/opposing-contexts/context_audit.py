"""Find settings that distinguish adaptive requests from fixed targets."""
from hashlib import sha256
from itertools import combinations, product
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import qualify as q

o, e, data = q.o, q.e, q.cases
D = o.D
BITS = (0, 1, 2, 4)
ARMS = ("deployed", "quiet", "fixed_1", "fixed_2", "fixed_3")


def event(points, state, holder, earlier, team):
    ask, reply = team
    target = int(ask[state])
    answer = int(reply[holder, earlier, target])
    earned = float(points[state | BITS[answer]])
    return {"ask": target, "reply": answer, "released": earned,
            "tail_net": earned - float(D.QUERY_COST[target] + D.SEND_COST[answer])}


def compare(points, label, prior, parameters, original):
    estimate = data.singleton(points)
    openers = o.replan.study.opening(estimate, prior, original)
    coords = tuple(points[i] for i in (0, 1, 2, 4))
    _, policies, value, mass = q.choose(coords, openers, prior, parameters)
    allowed = [arm for arm in policies if value[arm]["released"] >= value["quiet"]["released"] - 1e-10]
    deployed = max(allowed, key=lambda x: (value[x]["net"], x == "quiet"))
    exact = o.exact_parts(mass, points)
    teams = {"deployed": policies[deployed], "quiet": exact["exact_no_request"]}
    for card in range(1, 4):
        ask = np.where(D.CHAIR_LEGAL[:, card], card, 0)
        teams[f"fixed_{card}"] = (ask, o.choose_response(ask, mass, points))
    observations = []
    for l, r, a_ok, b_ok in product(range(8), range(8), (0, 1), (0, 1)):
        a, b = int(openers[0][l]), int(openers[1][r])
        probability = float(prior[l, r] * (1 - D.LOSS if a_ok else D.LOSS)
                            * (1 - D.LOSS if b_ok else D.LOSS))
        if probability == 0.:
            continue
        state = (BITS[a] if a_ok else 0) | (BITS[b] if b_ok else 0)
        outcomes = {arm: event(points, state, r, b, team) for arm, team in teams.items()}
        observations.append({"inventory": [l, r], "openings": [a, b], "delivered": [a_ok, b_ok],
                             "state": state, "mass": probability, "outcomes": outcomes})
    assert abs(sum(row["mass"] for row in observations) - 1.) < 1e-10
    supported = [v for v in observations if v["outcomes"]["deployed"]["ask"]
                 and v["outcomes"]["deployed"]["tail_net"] > v["outcomes"]["quiet"]["tail_net"] + 1e-10]
    pairs = []
    for first, second in combinations(supported, 2):
        left, right = (x["outcomes"] for x in (first, second))
        if left["deployed"]["ask"] == right["deployed"]["ask"]:
            continue
        values = {arm: left[arm]["tail_net"] + right[arm]["tail_net"] for arm in ARMS}
        margin = values["deployed"] - max(values[arm] for arm in ARMS[2:])
        if margin > 1e-10:
            pairs.append({"rows": [first, second], "tail_net": values, "margin": margin})
    chosen = min(pairs, key=lambda x: tuple((v["inventory"], v["delivered"]) for v in x["rows"])) if pairs else None
    mean = {arm: sum(row["mass"] * row["outcomes"][arm]["tail_net"] for row in observations) for arm in ARMS}
    return {"deployed": deployed, "reported_prior": label, "possible_events": len(observations),
            "positive_vs_quiet_mass": sum(row["mass"] for row in supported),
            "positive_query_targets": sorted({row["outcomes"]["deployed"]["ask"] for row in supported}),
            "strong_pairs": len(pairs), "chosen": chosen, "expected_tail_net_if_reply_delivers": mean}


def run():
    former, sparse = HERE.parents[1] / "fit.json", HERE.parent / "sparse-results.json"
    parameters = tuple([np.array(row) for row in e.read(file)["parameters"]] for file in (former, sparse))
    original = e.read(o.replan.study.OLD)["training"]["budget_fit"]
    results = {case: {label: compare(points, label, law, parameters, original)
                     for label, law in o.R.TEST_PRIORS.items()} for case, points in data.banks().items()}
    pins = (Path(__file__), HERE / "protocol.md", former, sparse, Path(q.__file__), *data.FILES.values())
    return {"cases": results, "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in pins}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
