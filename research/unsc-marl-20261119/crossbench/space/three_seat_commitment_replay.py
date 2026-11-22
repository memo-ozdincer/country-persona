"""Measure proof loss from truthful numbers in nonbinding statements."""
from collections import defaultdict
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import torch

import three_seat_commitment_judge as judge

HERE = Path(__file__).resolve().parent
transport = judge.transport.previous
fitted = transport.trained
shared = transport.shared
base = transport.base
LANGUAGE = judge.ROOT / "results.json"


def projected(grid, data, probabilities, replaces, admits):
    totals = defaultdict(float)
    for world, prior in data.prior.items():
        sender_state = data.states["A", world[0]]
        for (column, pay), a in zip(base.ACTIONS, probabilities[sender_state, :len(base.ACTIONS)], strict=True):
            first = grid.claim(world, 0, column)
            first_admitted = first if admits or first != replaces else None
            for seen, peer_p in base.observations(first_admitted, pay):
                receiver_state = data.states["B", world[1], seen]
                for slot, b in enumerate(probabilities[receiver_state, :3]):
                    second = grid.claim(world, 1, slot)
                    second_admitted = second if admits or second != replaces else None
                    for received_a, received_b in product((False, True), repeat=2):
                        evidence = (first_admitted if received_a else None, second_admitted if received_b else None)
                        authoritative = tuple(None if claim == replaces else claim for claim in evidence)
                        proposed = grid.information(evidence)[1]
                        allowed = grid.information(authoritative)[1]
                        assert proposed <= grid.winners(world)
                        p = prior * a * peer_p * b * (base.DELIVER if received_a else 1 - base.DELIVER) * (
                            base.DELIVER if received_b else 1 - base.DELIVER)
                        totals["mass"] += p
                        totals["peer_attempt"] += p * pay
                        totals["any_certificate"] += p * bool(proposed)
                        totals["certifies_without_warrant"] += p * bool(proposed - allowed)
                        totals["warranted_certificate"] += p * bool(proposed & allowed)
    assert abs(totals.pop("mass") - 1) < 1e-9
    return dict(totals) | {"warranted_net": totals["warranted_certificate"] - base.FEE * totals["peer_attempt"]}


def run():
    torch.set_num_threads(1)
    fit = json.loads(transport.FIT.read_text())
    entries = {row["draw"]: row for row in json.loads(fitted.REGISTRY.read_text())["accepted"]}
    traces = json.loads(LANGUAGE.read_text())
    negatives = [r for r in traces["records"] if r["group"] == "matched_author_controls" and r["gold"] == "reject"]
    assert len(negatives) == len(judge.PAIRS)
    frozen = torch.as_tensor(fit["weights"], dtype=torch.float64)
    reports = []
    for case in fit["reserved"]:
        identifier = case["grid_id"]
        with patch.dict(shared.FIXTURES, {"target": fitted.fixture(entries[identifier])}):
            grid = shared.Grid("target")
            data = fitted.data_for(grid)
            weights = data.probabilities(frozen).numpy()
            for foil in negatives:
                corrupted = ("ABC".index(foil["p"]), foil["grade"])
                modes = {mode: foil[mode]["stable"] == "admit" for mode in (*judge.RULES, "quote_only")}
                dimensions = {name: projected(grid, data, weights, corrupted, admits)
                              for name, admits in modes.items()}
                continue_only = projected(grid, data, weights, corrupted, False)
                assert continue_only["certifies_without_warrant"] == 0.
                reports.append({"grid": identifier, "foil": foil["id"], "replaces_tuple": corrupted,
                                "policies": dimensions, "reference_reject": continue_only})
    metrics = tuple(reports[0]["policies"]["quote_only"])
    means = {mode: {metric: float(sum(r["policies"][mode][metric] for r in reports) / len(reports))
                    for metric in metrics} for mode in (*judge.RULES, "quote_only")}
    return {"scope": "Deterministic stress test. Each foil replaces all uses of its one selected tuple within "
                     "one counterfactual run. These are numerically truthful but nonbinding messages. "
                     "Judgment is fixed from the live reader panel. Do not treat the replacement rate "
                     "as an estimate of any model's natural error rate.",
            "mean_over_stress_cases": means, "cases": reports}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
