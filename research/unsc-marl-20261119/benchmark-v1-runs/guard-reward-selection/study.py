"""Replay the isolated factual guard and fit senders with each terminal reward."""
import argparse
from itertools import product
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
ROOT = RUNS.parent
OLD_GUARD = RUNS / "isolated-guard-calibration"
OLD_FIT = RUNS / "protected-tribunals-routing"
BANK = RUNS / "tribunals-source-action-bank"
sys.path[:0] = [str(path) for path in (OLD_GUARD, OLD_FIT, BANK)]

import bank
import guard

original_requests = guard.requests


def requests():
    return original_requests()


def plan():
    assert guard.suite.verify_release() == "1.7"
    paths = (
        Path(__file__), HERE / "protocol.md", OLD_GUARD / "guard.py",
        OLD_FIT / "learn.py", OLD_FIT / "render.py", BANK / "headroom.py",
        BANK / "bank.py", BANK / "verdicts.json", BANK / "results.json",
        BANK / "packets.json", guard.historical.HERE / "slice_run.py",
        guard.historical.RELEASE / "release.json",
    )
    return {
        "pins": {str(path.relative_to(ROOT)): guard.suite.pin(path) for path in paths},
        "model_index": guard.suite.pin(guard.historical.MODEL / "model.safetensors.index.json"),
        "requests": [guard.e.checksum(row) for row in requests()],
        "fit": {"train": 0.65, "updates": 256, "learning_rate": 0.15},
        "evaluation_retention": [0.45, 0.65, 0.85],
    }


def score(rows, spec):
    import numpy as np
    import learn
    from headroom import optimize, slates

    grouped = {}
    for row, request in zip(rows, requests(), strict=True):
        assert all(row[name] == value for name, value in request.items())
        logits = {label: row["logits"][letter] for letter, label in row["labels"].items()}
        grouped.setdefault(row["id"], []).append(logits)
    _, linked, _ = bank.packets()
    archived = guard.e.read(BANK / "results.json")["by_order"]
    own = [[row["id"] for row in deck] for deck in bank.e.cases()[bank.CASE]["owned"]]
    assert tuple(map(len, own)) == (2, 4)
    reviewed = np.zeros((2, 2, 4))
    automatic = np.zeros_like(reviewed)
    records = {}
    for order, i, j in product(range(2), range(2), range(4)):
        a, b = own[0][i], own[1][j]
        record = archived[str(order)][f"{a}/{b}"]
        first, reverse = grouped[linked[f"{order}/{a}/{b}"]["id"]]
        mean = {label: (first[label] + reverse[label]) / 2 for label in guard.LABELS}
        chosen = max(mean, key=mean.get)
        hard = sorted(set(record["release_blockers"]) - {"guard_failed", "guard_uncertain"})
        expected = record["raw_70"][0] if record["guard"] == "clear" and not hard else 0
        assert expected == record["released_70"]
        reviewed[order, i, j] = expected
        automatic[order, i, j] = record["raw_70"][0] if chosen == "clear" and not hard else 0
        records[f"{order}/{a}/{b}"] = {
            "reviewed_guard": record["guard"], "automatic_guard": chosen,
            "label_order_decisions": [max(logits, key=logits.get) for logits in (first, reverse)],
            "mean_logits": mean, "other_blockers": hard,
            "reviewed_70": expected, "automatic_70": automatic[order, i, j],
        }
    rewards = {"reviewed": reviewed, "automatic": automatic}
    indicators = {
        "newly_released_probability": ((automatic > 0) & (reviewed == 0)).astype(float),
        "reviewed_positive_probability": (reviewed > 0).astype(float),
    }
    modes = {"independent": False, "peer": True}
    fits = {}
    for source, mode in product(rewards, modes):
        weights, trace = learn.fit(rewards[source], modes[mode], spec["fit"])
        fits[f"{source}/{mode}"] = {"weights": weights.tolist(), "trace": trace}
    evaluations = []
    for keep in spec["evaluation_retention"]:
        exact = {}
        for source, reward in rewards.items():
            exact[source] = [
                optimize({(a, b): reward[order, i, j] for i, a in enumerate(own[0])
                          for j, b in enumerate(own[1])},
                         slates(own[0], keep), slates(own[1], keep), order)
                for order in range(2)
            ]
        measured = {}
        for fit_id, fit in fits.items():
            mode = fit_id.split("/")[1]
            weights = np.array(fit["weights"])
            measured[fit_id] = {
                name: [round(value, 8) for value in
                       learn.evaluate(table, weights, keep, modes[mode], True)[0]]
                for name, table in (rewards | indicators).items()
            }
            for source in rewards:
                assert all(value <= bound[mode] + 1e-7 for value, bound in
                           zip(measured[fit_id][source], exact[source], strict=True))
        evaluations.append({"retention": keep, "exact": exact, "measured": measured})
    return {"records": records, "fits": fits, "evaluations": evaluations}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify", "score"))
    mode = parser.parse_args().mode
    guard.packets = lambda: bank.packets()[0]
    guard.HERE = HERE
    guard.OUT = HERE / "evidence"
    spec = plan()
    if mode == "plan":
        guard.e.emit(spec)
        return
    assert spec == guard.e.read(HERE / "plan.json")
    if mode == "run":
        guard.run()
        return
    rows = guard.historical.report.load(guard.OUT / "labels.jsonl")
    guard.e.emit(guard.verify(rows) if mode == "verify" else score(rows, spec))


if __name__ == "__main__":
    main()
