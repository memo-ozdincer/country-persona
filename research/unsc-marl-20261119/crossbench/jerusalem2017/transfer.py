"""Replay a frozen calibrated receiver on a new UN dossier and language senders."""
import argparse
from itertools import permutations
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
GAZA = HERE.parent / "gaza2023"
sys.path.insert(0, str(GAZA))

from calibrate_partner import Calibration, read
import routing

HORIZON = 8
PROBE_FEE = .05
EXPECTED = {"draft_desk": {"probe": [1, 0, 0, 0], "mission": [1, 0, 0, 0]},
            "statement_desk": {"probe": [0, 1, 1, 1], "mission": [0, 1, 1, 1]}}


def load():
    task_path = HERE / "task.json"
    task = json.loads(task_path.read_text())
    accession = json.loads((HERE / "accession.json").read_text())
    assert accession["task_sha256"] == routing.digest(task_path)
    return task


def controls():
    task = load()
    assert len(task["public_criteria"]) == 5 and all(len(row["criteria"]) == 5 for row in task["focuses"])
    records = {}
    for row in task["focuses"]:
        for receipt in ("slip", "matched"):
            sources = [row["slip"], row["backup"]] if receipt == "matched" else [row["slip"]]
            supplement = " ".join(sources)
            assert len(supplement.split()) <= 85
            records[f"{row['id']}/{receipt}"] = {"full_record": task["public_record"] + " " + supplement,
                                                "admitted_sources": sources, "supplement_words": len(supplement.split())}
    return records


def translate(table, order):
    """Change positional decoder outputs back to historical topic IDs."""
    slot_of_focus = np.argsort(order)
    slot_pair_index = {tuple(pair): index for index, pair in enumerate(routing.PAIR)}
    translated = []
    for pair in routing.PAIR:
        index = slot_pair_index[tuple(sorted(slot_of_focus[pair]))]
        translated.append(order[table[index]])
    result = np.asarray(translated)
    for pair, actions in zip(routing.PAIR, result, strict=True):
        assert all(value in pair for value in actions)
    return result


def score(desk, learned, calibration, points=None):
    probe = np.asarray(desk["probe"], dtype=int)
    mission = np.asarray(desk["mission"], dtype=int)
    assert probe.shape == mission.shape == (4,) and set(probe) <= {0, 1} and set(mission) <= {0, 1}
    chance = probe * (1 - calibration.question_loss)
    weights = np.prod(np.where(routing.REQUESTS, chance, 1 - chance), axis=1)
    probe_cost = 4 * PROBE_FEE + float(calibration.question_fee * probe.sum())
    frozen = calibration.fitted_receiver
    blind = calibration.receiver(np.full(4, .5), calibration.design_prior)
    def value(table, prior):
        if points is None:
            return calibration.utility(mission, table, prior)
        arrived = (1 - calibration.question_loss) * mission[:, None]
        focus = np.arange(4)[:, None]
        on_target = arrived * (table[:, 1] == focus) + (1 - arrived) * (table[:, 0] == focus)
        delivered = (1 - calibration.reply_loss) * on_target
        credit = (points[:, :1] + delivered * (points[:, 1:] - points[:, :1])) * prior
        return float(credit.sum() - calibration.question_fee * (prior.sum(axis=1) @ mission) - calibration.reply_fee)

    cases = {}
    for order in permutations(range(4)):
        order = np.asarray(order)
        signature = "".join(map(str, order))
        tables = {"transferred": [], "exact_decoder": []}
        disagreement = 0.
        for probability, probe_seen in zip(weights, routing.REQUESTS, strict=True):
            if probability == 0:
                continue
            in_slots = probe_seen[order]
            idx = int(in_slots @ np.asarray([8, 4, 2, 1]))
            state = tuple(-1 if seen else 1 for seen in in_slots)
            local_exact = calibration.receiver(calibration.probabilities(state), calibration.design_prior)
            candidates = {"transferred": learned[idx], "exact_decoder": local_exact}
            disagreement += probability * float(np.mean(learned[idx] != local_exact))
            for name, table in candidates.items():
                tables[name].append((probability, translate(table, order)))
        values = {}
        for name, prior in calibration.priors.items():
            base = {"frozen_no_probes": translate(frozen, order), "exact_blind_no_probes": translate(blind, order),
                    "prior_informed_known_sender": calibration.receiver(mission, prior)}
            values[name] = {key: value(tab, prior) for key, tab in base.items()}
            values[name].update({method: float(sum(weight * value(tab, prior)
                                                   for weight, tab in config) - probe_cost / HORIZON)
                                 for method, config in tables.items()})
        cases[signature] = {"expected_action_disagreement": disagreement, "priors": values}
    return {"probe_cost": probe_cost, "by_topic_order": cases}


def run(language=None):
    task = load()
    calibration = Calibration()
    calibration.points[:] = np.tile([42, 70], (4, 1))
    path = GAZA / "factored-calibration-results.json"
    frozen = np.asarray(read(path.name)["greedy_receiver_table"])
    dossiers = EXPECTED if language is None else language["desks"]
    results = {name: score(desk, frozen, calibration) for name, desk in dossiers.items()}
    return {"scope": "Two retrospective language partners follow opposing local rules. "
                     "Use the Gaza-trained receiver without updates. The exact decoder shares the development prior "
                     "and uses the Jerusalem receipt values. Reorder the historical topics across all 24 slot assignments. "
                     "This uses compiled records and simulated request and reply losses.",
            "task": task["id"], "task_sha256": routing.digest(HERE / "task.json"),
            "receiver_sha256": routing.digest(path), "language_trace_sha256": language["trace_sha256"] if language else None,
            "typed_or_language": "typed" if language is None else "measured_language_actions",
            "desks": dossiers, "compiled_records": controls(), "scores": results}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--language-actions", type=Path)
    args = cli.parse_args()
    language = json.loads(args.language_actions.read_text()) if args.language_actions else None
    print(json.dumps(run(language), indent=2, ensure_ascii=False))
