"""Compare prompt representations at the same call and reward-calibration budgets."""
import json
from unittest.mock import patch

from collect_claims import HERE, SOURCE, fixtures, prior, read

reform = prior.previous.earlier.previous.load("direct_reply_readout", SOURCE / "readout.py")


def run():
    old = read(SOURCE / "results.json")
    with patch.object(reform, "HERE", HERE):
        new = reform.run()
    assert old["calibration_rollouts"] == new["calibration_rollouts"]
    archive = read(HERE / "verified.json")["outputs"]
    intercept, slope = new["coefficients"]
    transfer = {}
    for key, row in fixtures().items():
        if row["family"] != "afghanistan":
            continue
        margins = reform.margin(key, archive)
        projected = intercept + slope * margins["mean"]
        transfer[key] = {
            "supported": row["supported"],
            "margins": margins,
            "projected_advantage": round(projected, 8),
            "decisions": {method: margin > 0 for method, margin in
                          (margins | {"reform_calibration": projected}).items()},
        }
    target_metrics = {
        method: {
            "correct": sum(r["decisions"][method] == r["supported"] for r in transfer.values()),
            "supported_recognized": sum(r["decisions"][method] and r["supported"] for r in transfer.values()),
            "unsupported_admitted": sum(r["decisions"][method] and not r["supported"] for r in transfer.values()),
        } for method in next(iter(transfer.values()))["decisions"]
    }
    held = [row for row in new["cases"].values() if row["split"] == "held"]
    return {
        "reform_prior_direct_metrics": old["held_metrics"],
        "reform_claim_scoped": new,
        "reform_held_margin_separation": {
            "min_supported": min(row["margins"]["mean"] for row in held if row["true_process_reply"]),
            "max_unsupported": max(row["margins"]["mean"] for row in held if not row["true_process_reply"]),
        },
        "afghanistan_transfer": {"fixtures": transfer, "metrics": target_metrics},
    }


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
