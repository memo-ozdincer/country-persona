"""Separate the contribution of query delivery and responder policy."""
from hashlib import sha256
from itertools import product
from pathlib import Path

import numpy as np

import match as k

n, t, r, o, a, e, D = k.n, k.t, k.r, k.o, k.a, k.e, k.D
HERE = Path(__file__).resolve().parent


def run():
    source = t.HERE / "numeric-results.json"
    bank = np.array(n.read(source)["score_banks"]["native"])
    calibration = {i: bank[i] for i in range(7) if i != 3}
    initialization = n.read(o.replan.study.OLD)["training"]["budget_fit"]
    output = {}
    for label, (truth, dominant) in a.laws().items():
        for visibility, prior in (("correct_mixture", truth), ("dominant_only", dominant)):
            openings = o.replan.study.opening(r.f.views(bank)["4"], prior, initialization)
            available, actual = o.opening(*openings, prior), o.opening(*openings, truth)
            cache = {}
            for delta in (-7, 0, 7):
                decisions = r.evaluate_locked(calibration, bank[3] + delta, prior, openings, available, cache)
                team_query, team_reply = decisions["interval_team"][1]
                fixed_query, fixed_reply = decisions["interval_fixed"][1]
                erased_reply = np.broadcast_to(team_reply[:, :, :1], team_reply.shape)
                controls = {
                    "team": (team_query, team_reply),
                    "erased": (team_query, erased_reply),
                    "fixed": (fixed_query, fixed_reply),
                    "fixed_chair_team_responder": (fixed_query, team_reply),
                    "team_chair_fixed_responder": (team_query, fixed_reply),
                }
                measures = {arm: o.measure(bank, actual, truth, openings, pair) for arm, pair in controls.items()}
                assert abs(measures["team"]["queries"] - measures["erased"]["queries"]) < 1e-10
                output[f"{label}/{visibility}/{delta}"] = measures
    paired = [(v["team"], v["erased"], v["fixed"]) for v in output.values()]
    summary = {
        "conditions": len(paired),
        "query_enabled_released_gain": sum(a["released"] - b["released"] for a, b, _ in paired) / len(paired),
        "query_enabled_net_gain": sum(a["net"] - b["net"] for a, b, _ in paired) / len(paired),
        "team_wins_vs_erased": sum(a["net"] > b["net"] + 1e-10 for a, b, _ in paired),
        "team_losses_vs_erased": sum(a["net"] < b["net"] - 1e-10 for a, b, _ in paired),
        "erased_wins_vs_fixed": sum(b["net"] > c["net"] + 1e-10 for _, b, c in paired),
    }
    pins = (Path(__file__), HERE / "mechanism.md", source, Path(r.__file__))
    return {"results": output, "summary": summary,
            "sha256": {file.name: sha256(file.read_bytes()).hexdigest() for file in pins}}


if __name__ == "__main__":
    e.emit(run())
