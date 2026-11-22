"""Freeze and replay the complete resolution 2593 routing distribution."""
import argparse
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import facilitator_claim_requests as prior_claims
import facilitator_live_delivery as live

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE / "facilitator-prospective-2593-evidence"
PACKET = EVIDENCE / "packet.json"
FAMILY = "facilitator-prospective-2593"
RUNNER = live.RUNNER
D = live.D
ROUTE = live.ROUTE
TRAINED = live.trained
MENU = (0, 3, 1, 2)
PRIORS = ("uniform", "correlated_duplicates")


def packet():
    return json.loads(PACKET.read_text())


def questions():
    return ("", *(card["question"] for card in packet()["cards"]))


def decode_requests():
    topics = {str(i): packet()["cards"][q - 1]["topic"] for i, q in enumerate(MENU) if q}
    for q, question in enumerate(questions()):
        yield live.prompt(f"query/{q}", 8, live.DECODER, {"topics": topics, "question": question})


def reply_requests(_):
    cards = packet()["cards"]
    for q, c in product(range(4), range(1, 4)):
        yield live.prompt(f"reply/{q}/{c}", 92, prior_claims.SYSTEM,
                          {"received_question": questions()[q], "authorized_source": cards[c - 1]["source"]})


def episode(generate):
    rows = generate(list(decode_requests()))
    rows.update(generate(list(reply_requests(rows))))
    return [{"family": FAMILY, "final": rows}]


def pins():
    files = (Path(__file__).resolve(), PACKET, EVIDENCE / "protocol.md", live.ACTION_FIT,
             Path(live.__file__), Path(prior_claims.__file__), Path(RUNNER.__file__),
             Path(TRAINED.__file__), Path(TRAINED.base.__file__), Path(D.__file__),
             Path(ROUTE.__file__), Path(TRAINED.base.diagnose.__file__))
    return {str(p.relative_to(HERE.parents[1])): RUNNER.digest(p) for p in files}


def verify(directory):
    base = live.common.reused.previous.prior
    with patch.multiple(base, local=decode_requests, audits=reply_requests, syntheses=lambda _: (),
                        pins=pins, FAMILY=FAMILY):
        return base.read(directory)


def rubric():
    scores = packet()["scoring"]
    return TRAINED.base.rubric(scores["public"], (scores["per_card"],) * 3,
                               scores["bridge_mask"], scores["bridge"])


def records():
    p = packet()
    records = []
    for mask in range(8):
        clauses = p["public"] + [c["record"] for i, c in enumerate(p["cards"]) if mask & (1 << i)]
        bridge = p["scoring"]["bridge_mask"]
        if mask & bridge == bridge:
            clauses.append(p["bridge"])
        record = " ".join(clauses)
        assert len(record.split()) <= p["scoring"]["record_word_cap"]
        records.append(record)
    return records


def policies(prior):
    public = rubric()
    left, right, opening, _ = TRAINED.base.context(public, prior)
    fitted = json.loads(live.ACTION_FIT.read_text())["learned"]
    _, _, chair, reply = D.scripts()
    independent = D.exact_independent(prior, TRAINED.base.terminal(public))
    assert np.array_equal(independent[0], left) and np.array_equal(independent[1], right)
    oracle, _ = TRAINED.base.diagnose.exact_tail(left, right, prior, TRAINED.base.terminal(public))
    return {"fitted": TRAINED.infer(fitted, public, (left, right), opening),
            "initial": TRAINED.infer(TRAINED.INITIAL, public, (left, right), opening),
            "script": (left, right, chair, reply), "independent": independent, "exact_public": oracle}


def distribution(policy, prior, decoded, admissions):
    left, right, chair, reply = policy
    mass = np.zeros(8)
    metrics = dict(cost=0., requests=0., decode_errors=0., failed_replies=0., attempts=0., delivered_replies=0.)
    for a, b in product(range(8), repeat=2):
        x, y = left[a], right[b]
        assert ROUTE.SEND[a, x] and ROUTE.SEND[b, y]
        for links in product((0, 1), repeat=4):
            first, second, query, last = links
            weight = prior[a, b] * (1 - D.LOSS) ** sum(links) * D.LOSS ** (4 - sum(links))
            mask = (ROUTE.BITS[x] * first) | (ROUTE.BITS[y] * second)
            q = chair[mask]
            assert D.CHAIR_LEGAL[mask, q]
            received = q * query
            c = reply[b, y, decoded[received]]
            assert ROUTE.SEND[b, c]
            admitted = admissions[received, c]
            mass[mask | (ROUTE.BITS[c] * last * admitted)] += weight
            metrics["cost"] += weight * (D.SEND_COST[x] + D.SEND_COST[y] + D.QUERY_COST[q] + D.SEND_COST[c])
            metrics["attempts"] += weight * (int(x != 0) + int(y != 0) + int(q != 0) + int(c != 0))
            metrics["requests"] += weight * (q != 0)
            metrics["decode_errors"] += weight * (decoded[received] != received)
            metrics["failed_replies"] += weight * (c != 0 and not admitted)
            metrics["delivered_replies"] += weight * (c != 0 and last and admitted)
    assert abs(mass.sum() - 1.) < 1e-12
    points = rubric()
    return {**metrics, "guarded_points": float(mass @ points), "strict_complete": float(mass[7]),
            "net": float(mass @ TRAINED.base.terminal(points) - metrics["cost"]), "mass": mass.tolist()}


def score(rows, review):
    decoded = []
    for q in range(4):
        row = rows[f"query/{q}"]
        value = row["output"]
        decoded.append(MENU[int(value)] if row["ended"] and value in "0123" and len(value) == 1 else 0)
    admissions = np.zeros((4, 4), dtype=bool)
    expected_ids = {f"reply/{q}/{c}" for q, c in product(range(4), range(1, 4))}
    assert set(review) == expected_ids
    for key, judgment in review.items():
        _, q, c = key.split("/")
        row = rows[key]
        assert len(judgment["witnesses"]) == 3
        assert all(w is None or (w and w in row["output"]) for w in judgment["witnesses"])
        admissions[int(q), int(c)] = (row["ended"] and len(row["output"].split()) <= 52
                                      and all(judgment["witnesses"]) and not judgment["unsupported"])
    results = {}
    for label in PRIORS:
        prior = ROUTE.TEST_PRIORS[label]
        results[label] = {}
        for arm, policy in policies(prior).items():
            typed = distribution(policy, prior, range(4), np.ones((4, 4), dtype=bool))
            reference = D.measure(policy, prior, rubric())
            assert all(abs(typed[k] - reference[k]) < 1e-10 for k in
                       ("guarded_points", "strict_complete", "net", "cost"))
            results[label][arm] = {"typed": typed, "english": distribution(policy, prior, decoded, admissions)}
    return {"decoded": decoded, "approved_reply_ids": [f"reply/{q}/{c}" for q, c in zip(*np.where(admissions))],
            "priors": results, "records": records(), "record_points": rubric().tolist()}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("mode", choices=("run", "verify", "score"))
    cli.add_argument("directory", type=Path)
    cli.add_argument("--model", type=Path)
    args = cli.parse_args()
    if args.mode == "run":
        assert rubric()[-1] == 70 and len(records()) == 8
        with patch.multiple(RUNNER, episode=episode, locks=pins):
            RUNNER.run(args.model, args.directory)
    elif args.mode == "verify":
        print(json.dumps({"verified_generations": len(verify(args.directory))}))
    else:
        review = json.loads((EVIDENCE / "review.json").read_text())
        print(json.dumps(score(verify(args.directory), review), ensure_ascii=False, indent=2))
