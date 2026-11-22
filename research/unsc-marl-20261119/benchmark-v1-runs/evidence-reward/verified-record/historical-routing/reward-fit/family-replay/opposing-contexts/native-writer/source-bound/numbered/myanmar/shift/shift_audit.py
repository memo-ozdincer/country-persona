"""Measure transfer of frozen calibration selectors to new docket score banks and laws."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import robust_selector as s

n, m = s.n, s.m


def pick(rows):
    values = {tuple(row) for row in rows}
    return sorted(values, key=lambda row: sha256(json.dumps(row).encode()).digest())[:8]


def cases(fit, sparse):
    train = {tuple(a) for source in (fit["train_banks"], sparse["training"]) for a in source}
    dense_rows = pick(fit["holdout_banks"])
    sparse_rows = pick(row["bank"] for row in sparse["synthetic_holdout"]["sparse"].values())
    assert len(dense_rows) == len(sparse_rows) == 8
    assert not (set(dense_rows) | set(sparse_rows)) & train
    held = [(kind, str(index), np.array(row, dtype=float))
            for kind, group in (("synthetic_dense", dense_rows), ("synthetic_sparse", sparse_rows))
            for index, row in enumerate(group)]
    historical = m.data.banks()
    inputs = (s.t.HERE / "intact-results.json", s.t.HERE.parent / "packed-results.json")
    assert np.array_equal(historical["myanmar"], n.read(inputs[0])["rank_normalized"]["bank"])
    assert np.array_equal(historical["unifil"], n.read(inputs[1])["native"]["population"]["bank"])
    return held + [("historical", name, bank) for name, bank in historical.items()]


def laws():
    named = m.o.R.TEST_PRIORS
    keys = tuple(named)
    assert keys == ("uniform", "asymmetric", "correlated_duplicates")
    weights = ((.65, .25, .10), (.10, .65, .25), (.25, .10, .65))
    return {base: (sum(w * named[name] for name, w in zip(keys, mix, strict=True)), named[base])
            for base, mix in zip(keys, weights, strict=True)}


def evaluate(bank, actual, announced, reviewed, parameters, original):
    singletons = s.t.cal.estimated(bank)
    openings = m.o.replan.study.opening(singletons, announced, original)
    declared = m.o.opening(*openings, announced)
    held = m.o.opening(*openings, actual)
    oracle = m.o.controls(bank, held, actual, openings)
    best_fixed = max((v["net"], tag) for tag, v in oracle.items() if tag != "exact_ask_reply")
    best_quiet = oracle["exact_no_request"]["released"]
    answer = {}
    for name, row in s.decide(singletons, reviewed, declared, announced, openings, parameters).items():
        result = m.o.measure(bank, held, actual, openings, row["policy"])
        assert result["net"] <= oracle["exact_ask_reply"]["net"] + 1e-10
        answer[name] = {"policy": row["key"], "net_over_fixed": result["net"] - best_fixed[0],
                        "quality_over_silence": result["released"] - best_quiet}
    return {"choice": answer, "oracle_fixed": best_fixed[1], "exact_margin": oracle["exact_ask_reply"]["net"] - best_fixed[0]}


def summarize(rows):
    grouped = {}
    for row in rows:
        for key in (("all", "all", "all"), (row["suite"], row["prior_information"], "all"),
                    (row["suite"], row["prior_information"], str(row["review_offset"]))):
            grouped.setdefault("/".join(key), []).append(row)
    results = {}
    for key, group in grouped.items():
        output = {"conditions": len(group)}
        for mode in ("nominal", "robust"):
            scores = [r["choice"][mode] for r in group]
            net = [r["net_over_fixed"] for r in scores]
            quality = [r["quality_over_silence"] for r in scores]
            output[mode] = {"wins": sum(x > 1e-10 for x in net), "losses": sum(x < -1e-10 for x in net),
                            "mean_margin": sum(net) / len(net), "worst_margin": min(net),
                            "quality_losses": sum(x < -1e-10 for x in quality), "worst_quality": min(quality)}
        results[key] = output
    return results


def run():
    dense_path, sparse_path = m.HERE.parents[1] / "fit.json", m.HERE.parent / "sparse-results.json"
    dense, sparse = n.read(dense_path), n.read(sparse_path)
    parameters = tuple([np.array(p) for p in v["parameters"]] for v in (dense, sparse))
    original = n.read(m.o.replan.study.OLD)["training"]["budget_fit"]
    tests, blends = cases(dense, sparse), laws()
    rows = []
    for (suite, identify, bank), (base, (truth, proxy)), information, delta in product(
            tests, blends.items(), ("correct_mixture", "dominant_only"), (-7, 0, 7)):
        announced = truth if information == "correct_mixture" else proxy
        value = evaluate(bank, truth, announced, bank[s.PAIR] + delta, parameters, original)
        rows.append({"suite": suite, "case": identify, "bank": bank.tolist(), "prior": base,
                     "prior_information": information, "review_offset": delta} | value)
    pins = (Path(__file__), HERE / "protocol.md", dense_path, sparse_path, Path(s.__file__), *m.data.FILES.values())
    return {"runs": rows, "summary": summarize(rows),
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in pins}}


if __name__ == "__main__":
    s.q.e.emit(run())
