"""Transfer a learned evidence likelihood to a non-diagonal record payoff."""
import argparse
from itertools import permutations
import json
from pathlib import Path
import sys

import numpy as np

import corroboration as case

HERE = case.HERE
sys.path.insert(0, str(HERE.parent / "jerusalem2017"))

import estimate_receiver
import transfer

HORIZON = 8
ARRANGEMENTS = list(permutations(range(4)))
DIRECT = {"national_desk": {"probe": [1, 1, 1, 0], "mission": [1, 1, 1, 0]},
          "procedure_desk": {"probe": [0, 0, 0, 1], "mission": [0, 0, 0, 1]}}


def policy(likelihood, design, scores):
    """Maximize incremental source value, conditional on local roster and bit."""
    # (inventory, signal, hidden focal source) x (focal source, possible response)
    mass = design.T[:, None, :] * likelihood.T[None, :, :]
    value = np.einsum("rqf,fa->rqa", mass, scores)
    return np.where(transfer.routing.OPTIONS[:, None, :], value, -np.inf).argmax(axis=-1)


def utility(sender, table, prior, gains, bare, c, loss=None, probe_cost=0.):
    chosen = np.arange(4)[:, None]
    query_loss = c.question_loss if loss is None else loss
    got = (1 - query_loss) * sender[:, None]
    result = (got * gains[chosen, table[:, 1]] + (1 - got) * gains[chosen, table[:, 0]])
    delivered = bare[:, None] + (1 - c.reply_loss) * result
    return float((prior * (delivered - c.question_fee * sender[:, None] - c.reply_fee)).sum() - probe_cost)


def known_probability(sender, question_loss):
    received = (1 - question_loss) * sender
    return np.column_stack([1 - received, received])


def bound(prior, scores, bare, calibration):
    best = -np.inf
    silent = None
    for sender in transfer.routing.REQUESTS:
        reply = policy(known_probability(sender, calibration.question_loss), prior, scores)
        value = utility(sender, reply, prior, scores, bare, calibration)
        if not sender.any():
            silent = value
        best = max(value, best)
    return {"prior_informed_silent": silent, "prior_informed_interactive": best}


def run(schedules, source=None):
    task = case.bank()
    c = transfer.Calibration()
    scores = np.asarray(task["joint_scores"])
    bare = np.asarray(task["bare_scores"])
    gains = scores - bare[:, None]
    assert np.all(gains >= 0)
    meta = transfer.read("factored-calibration-results.json")
    model_path = transfer.HERE / "estimated-receiver.json"
    fitted = np.asarray(case.read(model_path)["emission"])
    background = c.design_prior.T
    conditional = background / background.sum(axis=1, keepdims=True)
    match_only = estimate_receiver.table(conditional, fitted, np.full(4, 28))
    outcomes = {}
    for label, pair in schedules.items():
        probe, mission = map(np.asarray, (pair["probe"], pair["mission"]))
        assert probe.shape == mission.shape == (4,) and set(probe) <= {0, 1} and set(mission) <= {0, 1}
        branch = known_probability(probe, c.question_loss)
        probability = np.prod(branch[np.arange(4), transfer.routing.REQUESTS], axis=1)
        assert np.isclose(probability.sum(), 1.)
        cost = (.05 * 4 + c.question_fee * probe.sum()) / HORIZON
        details = {}
        for perm in ARRANGEMENTS:
            order = np.asarray(perm)
            matrix = gains[np.ix_(order, order)]
            blind = policy(known_probability(np.full(4, .5), c.question_loss), c.design_prior, matrix)
            no_probe = transfer.translate(blind, order)
            tables = []
            for obs, weight in zip(transfer.routing.REQUESTS, probability, strict=True):
                if not weight:
                    continue
                slots = obs[order]
                index = int(slots @ np.asarray([8, 4, 2, 1]))
                state = tuple(-1 if bit else 1 for bit in slots)
                exact = c.probabilities(state)
                routes = {
                    "estimated_joint_reward": policy(fitted[slots], c.design_prior, matrix),
                    "exact_joint_reward": policy(known_probability(exact, c.question_loss), c.design_prior, matrix),
                    "estimated_match_only": match_only[index],
                    "frozen_gaza_match": np.asarray(meta["greedy_receiver_table"])[index],
                }
                tables.append((weight, {key: transfer.translate(route, order) for key, route in routes.items()}))
            for name, prior in c.priors.items():
                measures = {"exact_no_probe": utility(mission, no_probe, prior, gains, bare, c)}
                for label_type in tables[0][1]:
                    measures[label_type] = sum(w * utility(mission, tab[label_type], prior, gains, bare, c, probe_cost=cost)
                                               for w, tab in tables)
                measures["estimated_joint_mission_erased"] = sum(
                    w * utility(mission, tab["estimated_joint_reward"], prior, gains, bare, c, loss=1., probe_cost=cost)
                    for w, tab in tables
                )
                measures.update(bound(prior, gains, bare, c))
                assert measures["prior_informed_interactive"] + 1e-9 >= max(measures.values())
                signature = "".join(map(str, order))
                details.setdefault(signature, {})[name] = measures
        rows = [result for context in details.values() for result in context.values()]
        summary = {}
        for compare in ("exact_no_probe", "exact_joint_reward", "estimated_match_only",
                        "prior_informed_silent", "estimated_joint_mission_erased"):
            diffs = np.array([row["estimated_joint_reward"] - row[compare] for row in rows])
            summary[compare] = {"mean_margin": float(diffs.mean()), "minimum_margin": float(diffs.min()),
                                "maximum_margin": float(diffs.max()), "wins": int(np.count_nonzero(diffs > 1e-9)),
                                "ties": int(np.count_nonzero(np.abs(diffs) <= 1e-9)), "conditions": len(diffs)}
        outcomes[label] = {"probe_cost_per_mission": float(cost), "summary": summary, "coordinates": details}
    return {"scope": "Frozen Gaza/Jerusalem channel estimate, exact symbolic comparison and declared development "
                     "inventory distribution. The receiver uses the public card-pair payoff and never receives the "
                     "left desk's own source. All priors and topic permutations are simulation sensitivity coordinates. "
                     "The prior-informed controls may use the evaluation prior and choose a new sender schedule.",
            "code_sha256": transfer.routing.digest(Path(__file__)),
            "task_sha256": task["task_sha256"], "relay_matrix_sha256": transfer.routing.digest(HERE / "corroboration-records.json"),
            "channel_sha256": transfer.routing.digest(model_path), "language_trace_sha256": source,
            "bare": bare.tolist(), "gains": gains.tolist(), "desks": schedules, "outcomes": outcomes}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--actions", type=Path)
    args = cli.parse_args()
    language = case.read(args.actions) if args.actions else None
    print(json.dumps(run(language["desks"], language["trace_sha256"]) if language else run(DIRECT), indent=2))
