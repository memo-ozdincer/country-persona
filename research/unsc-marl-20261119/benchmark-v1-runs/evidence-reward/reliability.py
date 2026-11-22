"""Evaluate the same held opening paths under different follow-up delivery rates."""
from hashlib import sha256
from pathlib import Path

import environment as env
import followup as f

HERE = Path(__file__).resolve().parent


def run():
    learned = env.E.read(HERE / "followup.json")
    heads = learned["fit"]["heads"]
    held = [r for split, r in env.records() if split == "held"]
    rates = (.20, .28, .95)
    first = learned["summary"]["no_followup"]
    arms = ("exact_cost_aware", "learned_team")
    result = {}
    for rate in rates:
        rows = {}
        for mode in arms:
            values = [f.evaluate(r, mode, heads, followup_delivery=rate) for r in held]
            sums = {field: sum(row[field] for row in values) for field in first if field != "mean_net"}
            assert abs(sums["proof"] - first["proof"]) < 1e-9
            sums["gain_over_silence"] = sums["net"] - first["net"]
            rows[mode] = sums
        result[str(rate)] = rows
    files = (Path(__file__), HERE / "followup.py", HERE / "followup.json", HERE / "reliability-protocol.md")
    return {"first_stage_baseline": first, "second_stage_rates": result,
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    env.E.emit(run())
