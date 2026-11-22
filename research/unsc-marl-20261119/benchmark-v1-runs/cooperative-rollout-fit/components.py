"""Replay each fitted head with its matched neutral partner."""
import json
from itertools import product
from pathlib import Path

import numpy as np

import rollout_fit as shared

HERE = Path(__file__).resolve().parent


def run():
    previous = shared.wire.n.read(HERE / "results.json")
    locked = shared.wire.n.read(HERE / "plan.json")
    andata = shared.wire.n.read(shared.INITIAL)["training"]["budget_fit"]
    weights = [tuple(np.array(part) for part in stage) for stage in previous["weights"]]
    setups = {"reply_only": [(r, np.zeros_like(q)) for r, q in weights],
              "chair_only": [(np.zeros_like(r), q) for r, q in weights]}
    rows = []
    names = [*setups, "learned", "no_fit"]
    laws = shared.a.laws()
    for r in previous["rows"]:
        bank = np.array(locked["test_banks"][r["case"]], dtype=float)
        true, proxy = laws[r["law"]]
        shown = true if r["information"] == "exact" else proxy
        opening, mass, forecast = shared.context(bank, np.clip(bank[3] + r["review_offset"], 0, 70), shown, andata)
        assert [x.tolist() for x in opening] == r["opening"]
        outs = r["outcomes"] | {kind: shared.metric(bank, true, opening, shared.deploy(forecast, mass, w))
                                for kind, w in setups.items()}
        rows.append({k: r[k] for k in ("case", "law", "information", "review_offset", "silence_quality")} | {"outcomes": outs})
    summary = {}
    for name in names:
        measures = [r["outcomes"][name] for r in rows]
        summary[name] = {
            "vs_no_fit": shared.compare([m["net"] - r["outcomes"]["no_fit"]["net"] for m, r in zip(measures, rows)]),
            "mean_release_delta": float(np.mean([m["released"] - r["outcomes"]["no_fit"]["released"]
                                               for m, r in zip(measures, rows)])),
            "mean_cost_delta": float(np.mean([m["cost"] - r["outcomes"]["no_fit"]["cost"]
                                            for m, r in zip(measures, rows)])),
            "below_silence": sum(m["released"] < r["silence_quality"] - 1e-9 for m, r in zip(measures, rows)),
        }
    return {"summary": summary, "rows": rows,
            "sha256": {p.name: shared.digest(p) for p in
                       (Path(__file__), HERE / "results.json", HERE / "plan.json", Path(shared.__file__))}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
