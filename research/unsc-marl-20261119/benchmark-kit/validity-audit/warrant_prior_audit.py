"""Rebuild learned estimates from public receipts and summarize net value."""
import argparse
import json
from pathlib import Path

import numpy as np

import warrant_prior_learning as study


def audit(data):
    replayed = 0
    results = {}
    for mode in ("independent", "matching", "mixed_matching"):
        cells = [entry["modes"][mode]["scores"] for entry in data["domains"]]
        baseline = np.mean([cell["uniform"]["net"] for cell in cells])
        table = {"uniform": float(baseline),
                 "true_prior": float(np.mean([cell["true_prior"]["net"] for cell in cells])),
                 "true_request_fixed_opening": float(np.mean([cell["true_request_fixed_opening"]["net"] for cell in cells]))}
        for n in study.SAMPLES:
            table[str(n)] = {}
            for estimator in ("matching_posterior", "unstructured_em"):
                options = [cell[str(n)][estimator] for cell in cells]
                row = {"mean_tv": float(np.mean([value["tv_to_actual"] for value in options]))}
                for arm in ("end_to_end", "fixed_opening"):
                    gains = np.asarray([value[arm]["net"] - cell["uniform"]["net"]
                                       for value, cell in zip(options, cells, strict=True)])
                    gain = float(gains.mean())
                    row[arm] = {"mean_net": float(baseline + gain), "gain": gain,
                                "wins": int((gains > 1e-12).sum()),
                                "losses": int((gains < -1e-12).sum()),
                                "ties": int((np.abs(gains) <= 1e-12).sum()),
                                "break_even_workshops_if_calibration_message_cost_is_point_ten":
                                    int(np.ceil(2 * n * .10 / gain)) if gain > 1e-12 else None}
                table[str(n)][estimator] = row
        results[mode] = table
    for entry in data["domains"]:
        worlds = [(a, b) for a in entry["grades"][0] for b in entry["grades"][1]]
        for run in entry["modes"].values():
            reports = run["calibration_receipts"]
            assert len(reports) == study.SAMPLES[-1]
            valid = np.asarray([[all(world[role][package] == grade for role, package, grade in stream)
                                 for world in worlds] for stream in reports])
            assert valid.any(1).all()
            for n in study.SAMPLES:
                estimated = study.estimate(valid[:n])
                for key, expected in estimated.items():
                    archived = np.asarray(run["scores"][str(n)][key]["estimated_prior"]).ravel()
                    assert np.allclose(archived, expected, atol=1e-13, rtol=0.)
                    replayed += 1
    return {"reconstructed_estimates_without_true_inventories": replayed, "averages": results}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("report", type=Path)
    print(json.dumps(audit(json.loads(cli.parse_args().report.read_text())), indent=2))
