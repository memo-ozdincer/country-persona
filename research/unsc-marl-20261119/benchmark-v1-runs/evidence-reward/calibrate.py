"""Fit the same follow-up team with both cheap and costly delivery outcomes."""
from hashlib import sha256
from pathlib import Path

import environment as env
import followup as f

HERE = Path(__file__).resolve().parent
TRAIN_RATES = (.10, .16, .24, .32, .45, .65, .90)
TEST_RATES = (.12, .20, .275, .28, .285, .35, .55, .80, .95)


def train_and_held():
    training, held = [], []
    for split, row in env.records():
        if split == "held":
            held.append(row)
            continue
        assert row["id"].startswith("synthetic-")
        for state, weight, _, _ in f.start_states(row, True):
            if state["decision"] != "U":
                training.append((state, weight))
    assert len(held) == 44 and len(training) == 136
    return training, held


def summarize(held, mode, heads, rate):
    rows = [f.evaluate(r, mode, heads, followup_delivery=rate) for r in held]
    return {field: sum(row[field] for row in rows) for field in rows[0]}


def run():
    training, held = train_and_held()
    events = [(state, rate, weight / len(TRAIN_RATES)) for state, weight in training for rate in TRAIN_RATES]
    heads, trace = f.fit(events)
    original = env.E.read(HERE / "followup.json")["fit"]["heads"]
    rates = {}
    for rate in TEST_RATES:
        choices = {"original": ("learned_team", original), "broad": ("learned_team", heads),
                   "exact": ("exact_cost_aware", heads), "silence": ("no_followup", heads)}
        arms = {arm: summarize(held, mode, parameters, rate) for arm, (mode, parameters) in choices.items()}
        for item in arms.values():
            item["regret"] = arms["exact"]["net"] - item["net"]
            assert abs(item["proof"] - arms["exact"]["proof"]) < 1e-9 and item["regret"] >= -1e-9
        rates[str(rate)] = arms
    files = (Path(__file__), HERE/"calibration-protocol.md", HERE/"followup.py", HERE/"followup.json")
    return {"train_rates": TRAIN_RATES, "test_rates": TEST_RATES, "train_paths": len(events),
            "train_trace": trace, "heads": heads, "stress": rates,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    env.E.emit(run())
