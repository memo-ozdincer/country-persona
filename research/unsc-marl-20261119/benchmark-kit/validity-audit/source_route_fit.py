"""Learn which exact source block two agents should transmit under a slot cap."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
CASE = HERE / "source-record-sudan-reserve.json"
SEED = 57041
STEPS = 120
MESSAGE_COST = .2
# A position requires its role's first block. A common-ground claim needs both
# qualification blocks. These are proof-availability units, not prose points.
REQUIRES = (1, 4, 10)
CHOICES = ((0, 1, 2), (0, 4, 8))


def reward(mask, weights):
    return sum(weight for need, weight in zip(REQUIRES, weights, strict=True)
               if mask & need == need)


def problem(public, weights, availability):
    vectors, legal = [], []
    for seat, options in enumerate(CHOICES):
        seat_vector = []
        other = CHOICES[1-seat]
        peer_can_add = other[1] | other[2]
        for action in options:
            units = (reward(public | action, weights) - reward(public, weights)) / 7
            complementary = (reward(public | peer_can_add | action, weights)
                             - reward(public | peer_can_add, weights)) / 7
            seat_vector.append((float(action != 0), float(action != 0 and not public & action),
                                units, complementary - units, float(action != 0 and bool(public & action)),
                                (reward(public | peer_can_add, weights) - reward(public, weights)) / 7
                                * float(action != 0), float(action == options[2])))
        vectors.append(seat_vector)
        legal.append([action == 0 or bool(availability[seat] & action) for action in options])
    rewards = [[reward(public | a | b, weights) - MESSAGE_COST * (bool(a) + bool(b)) for b in CHOICES[1]]
               for a in CHOICES[0]]
    return np.array(vectors), np.array(legal), np.array(rewards)


def synthetic():
    rng = np.random.default_rng(SEED)
    out = []
    for _ in range(192):
        public = int(rng.integers(16))
        weights = tuple(int(i) for i in rng.integers(2, 9, size=3))
        availability = (int(rng.choice((1, 2, 3), p=(.1, .1, .8))),
                        int(rng.choice((4, 8, 12), p=(.1, .1, .8))))
        out.append(problem(public, weights, availability))
    return tuple(np.stack(parts) for parts in zip(*out, strict=True))


def train():
    features, legal, rewards = synthetic()
    theta = np.zeros(features.shape[-1])
    trace = []
    for step in range(STEPS):
        scores = np.where(legal, features @ theta, -np.inf)
        p = np.exp(scores - scores.max(axis=2, keepdims=True))
        p /= p.sum(axis=2, keepdims=True)
        team = p[:, 0, :, None] * p[:, 1, None, :]
        q = np.stack((np.einsum("nij,nj->ni", rewards, p[:, 1]),
                      np.einsum("nij,ni->nj", rewards, p[:, 0])), axis=1)
        mean = (p * q).sum(axis=-1, keepdims=True)
        gradient = np.einsum("nsa,nsaf->f", p * (q - mean), features) / len(p)
        assert np.isfinite(gradient).all()
        theta += .2 * gradient
        trace.append({"step":step+1,"team_return":float((team*rewards).sum(axis=(1,2)).mean()),
                      "gradient_norm":float(np.linalg.norm(gradient))})
    return theta, trace


def script(public, weights, options):
    # Maximum immediate distinct coverage subject to the same per-seat budget.
    # Prefer a new source on a tie, then the declared action order.
    return max(range(len(options)), key=lambda i: (reward(public | options[i], weights) - MESSAGE_COST*bool(i),
                                                   -i))


def report():
    theta, trace = train()
    case = json.loads(CASE.read_text())
    mapping = {bit: source for bit, source in zip((1,2,4,8), (
        k for role in case["delegate_evidence"].values() for k in role),strict=True)}
    assert mapping == {1:"RU-A",2:"RU-B",4:"CN-A",8:"CN-B"}
    weights = (7,7,7)
    output = []
    for public in range(16):
        inputs, legal, payoff = problem(public, weights, (3,12))
        learned = tuple(int(i) for i in np.where(legal, inputs@theta, -np.inf).argmax(axis=1))
        independent = tuple(script(public,weights,options) for options in CHOICES)
        first = independent[0]
        sequential = (first, script(public|CHOICES[0][first], weights,CHOICES[1]))
        oracle = tuple(int(i) for i in np.unravel_index(payoff.argmax(), payoff.shape))
        rows = {}
        for name, (i,j) in (("learned",learned),("independent",independent),("sequential",sequential),("oracle",oracle)):
            sent = (CHOICES[0][i], CHOICES[1][j])
            visible = public | sent[0] | sent[1]
            rows[name] = {"sent":[mapping.get(bit) for bit in sent],
                          "visible":[source for bit,source in mapping.items() if visible & bit],
                          "points":reward(visible,weights),"return":float(payoff[i,j]),
                          "proofs":[visible&need==need for need in REQUIRES]}
        output.append({"public_mask":public,"public":[v for k,v in mapping.items() if public&k],"arms":rows})
    return {"scope":"Two simultaneous shared-policy agents, trained on synthetic coverage and evaluated on the 16 public-source masks of the pre-existing Sudan docket. No Qwen model updates.",
            "seed":SEED,"training_instances":192,"message_cost":MESSAGE_COST,"coefficients":theta.tolist(),
            "trace":trace,"case_sha256":sha256(CASE.read_bytes()).hexdigest(),"sudan":output}


if __name__=="__main__":
    print(json.dumps(report(),indent=2))
