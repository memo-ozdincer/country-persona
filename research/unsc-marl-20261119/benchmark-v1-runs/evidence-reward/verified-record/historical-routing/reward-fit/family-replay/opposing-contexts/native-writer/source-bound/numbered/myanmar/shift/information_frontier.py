"""Separate reward information and inventory-prior errors from learned routing."""
from hashlib import sha256
from pathlib import Path

import numpy as np

import shift_audit as a

n, m, s, HERE = a.n, a.m, a.s, a.HERE
PAIR_MASKS = [3, 5, 6]


def views(bank):
    solo = s.t.cal.estimated(bank)
    one = s.t.cal.estimated(bank, 3)
    seven = bank.copy()
    # Use unbounded addition for the interaction calculation. Bound only the predicted triple.
    base = bank[0]
    with_no_pairs = sum(bank[[1, 2, 4]]) - 2 * base
    even = [bank[1] + bank[2] - base, bank[1] + bank[4] - base, bank[2] + bank[4] - base]
    seven[7] = np.clip(with_no_pairs + np.sum(bank[PAIR_MASKS] - even), 0, 70)
    assert np.array_equal(seven[:7], bank[:7])
    return {"4": solo, "5": one, "7": seven, "8": bank}


def run():
    original = n.read(m.o.replan.study.OLD)["training"]["budget_fit"]
    checkpoint = n.read(HERE / "results.json")
    laws = a.laws()
    rows = []
    for locked in checkpoint["runs"]:
        if locked["review_offset"]:
            continue
        bank = np.array(locked["bank"], dtype=float)
        actual, proxy = laws[locked["prior"]]
        advertised = actual if locked["prior_information"] == "correct_mixture" else proxy
        opening = m.o.replan.study.opening(views(bank)["4"], advertised, original)
        mass = m.o.opening(*opening, advertised)
        held = m.o.opening(*opening, actual)
        controls = m.o.controls(bank, held, actual, opening)
        fixed = max(v["net"] for k, v in controls.items() if k != "exact_ask_reply")
        exact = controls["exact_ask_reply"]["net"]
        assert abs(exact - fixed - locked["exact_margin"]) < 1e-10
        entries = {}
        for k, forecast in views(bank).items():
            query, reply = m.o.exact_parts(mass, forecast)["exact_ask_reply"]
            outcome = m.o.measure(bank, held, actual, opening, (query, reply))
            if k == "8" and locked["prior_information"] == "correct_mixture":
                assert abs(exact - outcome["net"]) < 1e-10
            entries[k] = {"net_over_fixed": outcome["net"] - fixed,
                          "quality_over_silence": outcome["released"] - controls["exact_no_request"]["released"]}
        rows.append({k: locked[k] for k in ("suite", "case", "prior", "prior_information", "bank")} | {"grades": entries})
    summary = {}
    for suite in ("historical", "synthetic_dense", "synthetic_sparse"):
        for prior in ("correct_mixture", "dominant_only"):
            selected = [r for r in rows if r["suite"] == suite and r["prior_information"] == prior]
            summary[f"{suite}/{prior}"] = {
                k: {"conditions": len(selected), "wins": sum(x["grades"][k]["net_over_fixed"] > 1e-10 for x in selected),
                    "losses": sum(x["grades"][k]["net_over_fixed"] < -1e-10 for x in selected),
                    "mean": sum(x["grades"][k]["net_over_fixed"] for x in selected) / len(selected)}
                for k in ("4", "5", "7", "8")}
    assert len(rows) == 120
    pins = (Path(__file__), HERE / "information-protocol.md", HERE / "results.json", Path(a.__file__))
    return {"runs": rows, "summary": summary, "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in pins}}


if __name__ == "__main__":
    s.q.e.emit(run())
