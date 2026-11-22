"""Exhaustively score verified relays under the full Jerusalem inventory distribution."""
import json
from itertools import permutations, product
from pathlib import Path

import numpy as np

import estimate_receiver
import transfer
import verified_relay as relay

HERE = transfer.HERE
HORIZONS = (1, 8, 32)
PROBE_FEE = .05
IDENTITY = "0123"
WEIGHTS = np.array([8, 4, 2, 1])


def physical_bank():
    task = transfer.load()
    snippets = {entry["id"]: entry["backup"] for entry in task["focuses"]}
    registry = {name: relay.hash_text(text) for name, text in snippets.items()}
    ids = list(snippets)
    # Axes are focal slip, responder inventory, and choice within its inventory.
    points = np.zeros((4, 6, 2), dtype=int)
    for focal, right, action in product(range(4), range(6), range(2)):
        receiver_inventory = transfer.routing.PAIR[right]
        source = ids[receiver_inventory[action]]
        envelope = relay.packet(source, snippets[source])
        matched = relay.admit(envelope, ids[focal], [ids[i] for i in receiver_inventory], registry)
        result = task["focuses"][focal]["slip"]
        if matched:
            result += " " + matched
        assert 0 < len(envelope["text"].split()) <= relay.CAP
        assert len(result.split()) <= relay.CHAIR_CAP
        assert (matched is not None) == (ids[focal] == source)
        points[focal, right, action] = 70 if matched else 42
    return points


def decoder_tables(calibration, observations):
    learned = transfer.read("factored-calibration-results.json")["greedy_receiver_table"]
    model = json.loads((HERE / "estimated-receiver.json").read_text())
    prior = calibration.design_prior.T
    conditional = prior / prior.sum(axis=1, keepdims=True)
    calibrated = estimate_receiver.table(conditional, np.asarray(model["emission"]), np.full(4, 28))
    exact = []
    for row in observations:
        state = tuple(-1 if bit else 1 for bit in row)
        exact.append(calibration.receiver(calibration.probabilities(state), calibration.design_prior))
    return {"estimated_channel": calibrated, "exact_calibration": np.asarray(exact),
            "older_fixed_rubric": np.asarray(learned)}


def expected_gain(sender, table, points, calibration, loss):
    source = transfer.routing.PAIR[:, None, :]
    location = (source == table[:, :, None]).argmax(axis=-1)
    assert np.all(np.any(source == table[:, :, None], axis=-1))
    arrived = (1 - loss) * sender[:, None]
    score = np.arange(4)[:, None]
    inventory = np.arange(6)
    with_request = points[score, inventory, location[:, 1]]
    without_request = points[score, inventory, location[:, 0]]
    gain = (arrived * with_request + (1 - arrived) * without_request) - 42
    return (1 - calibration.reply_loss) * gain - calibration.question_fee * sender[:, None] - calibration.reply_fee


def across_orders(probe_sender, mission_sender, points, calibration, keep_orders=True):
    observations = transfer.routing.REQUESTS
    tables = decoder_tables(calibration, observations)
    exact_without = calibration.receiver(np.full(4, .5), calibration.design_prior)
    masses = probe_sender * (1 - calibration.question_loss)
    delivered_prob = np.prod(np.where(observations, masses, 1 - masses), axis=1)
    assert np.isclose(delivered_prob.sum(), 1.)
    costs = PROBE_FEE * 4 + calibration.question_fee * probe_sender.sum()
    reports = {}
    all_orders = list(permutations(range(4))) if keep_orders else [(0, 1, 2, 3)]
    for order in all_orders:
        order = np.asarray(order)
        chosen = {name: np.zeros((4, 6)) for name in tables}
        erased = np.zeros((4, 6))
        for observed, probability in zip(observations, delivered_prob, strict=True):
            if probability == 0:
                continue
            index = observed[order] @ WEIGHTS
            for name, table in tables.items():
                decision = transfer.translate(table[index], order)
                utility = expected_gain(mission_sender, decision, points, calibration, calibration.question_loss)
                chosen[name] += probability * utility
                if name == "estimated_channel":
                    erased += probability * expected_gain(mission_sender, decision, points, calibration, 1.)
        no_probe_exact = transfer.translate(exact_without, order)
        no_probe_frozen = transfer.translate(calibration.fitted_receiver, order)
        values = {"exact_no_probe": expected_gain(mission_sender, no_probe_exact, points, calibration,
                                                   calibration.question_loss),
                  "frozen_no_probe": expected_gain(mission_sender, no_probe_frozen, points, calibration,
                                                    calibration.question_loss)}
        out = {}
        for horizon in HORIZONS:
            measured = {}
            for name, prior in calibration.priors.items():
                row = {key: 42 + float((v * prior).sum()) for key, v in values.items()}
                row.update({key: 42 + float((v * prior).sum()) - costs / horizon for key, v in chosen.items()})
                row["estimated_channel_mission_erased"] = 42 + float((erased * prior).sum()) - costs / horizon
                candidate = calibration.receiver(np.zeros(4), prior)
                row["prior_informed_silent_pair"] = 42 + float(
                    (prior * expected_gain(np.zeros(4), candidate, points, calibration, 1.)).sum()
                )
                measured[name] = row
            out[str(horizon)] = measured
        reports["".join(map(str, order))] = out
    return {"probe_cost": float(costs), "evaluations": reports}


def report():
    calibration = transfer.Calibration()
    calibration.points[:, 1] = 70
    points = physical_bank()
    datasets = ("factored-evidence/actions.json", "language-evidence/actions.json")
    stable = json.loads((HERE / datasets[0]).read_text())["desks"]
    unstable = json.loads((HERE / datasets[1]).read_text())["desks"]["statement_desk"]
    cases = {**stable, "paraphrase_drift_statement_desk": unstable}
    outcomes = {}
    for label, observed in cases.items():
        probe, mission = (np.asarray(observed[stage]) for stage in ("probe", "mission"))
        result = across_orders(probe, mission, points, calibration)
        gap = {
            str(h): [entry["estimated_channel"] - entry["exact_no_probe"]
                     for order in result["evaluations"].values() for entry in order[str(h)].values()]
            for h in HORIZONS
        }
        result["calibrated_minus_exact_no_probe"] = {
            k: {"minimum": float(min(v)), "maximum": float(max(v)), "mean": float(np.mean(v)),
                "wins": int(np.count_nonzero(np.asarray(v) > 1e-9)),
                "ties": int(np.count_nonzero(np.abs(v) <= 1e-9)), "conditions": len(v)}
            for k, v in gap.items()
        }
        outcomes[label] = result
    return {"scope": "Exhaustively authenticate all legal Jerusalem notes and compose each allowed receipt. "
                     "Integrate the original request, reply and probe loss laws. No new model generations. "
                     "Exact no-probe knows the design inventory prior and uniform prior over the 16 possible senders; "
                     "it sees the same mission request without the calibration bits. The ten priors are synthetic. "
                     "The 24 placements of archival topics change which topic gets each simulated slot.",
            "code_sha256": transfer.routing.digest(Path(__file__)),
            "files": {file: transfer.routing.digest(HERE / file)
                      for file in (*datasets, "task.json", "estimated-receiver.json", "verified_relay.py")},
            "legal_receipts": int(points.size), "outcomes": outcomes}


if __name__ == "__main__":
    print(json.dumps(report(), ensure_ascii=False, indent=2))
