"""Apply quote-bound review and test whether the selected writer has peer headroom."""
from itertools import product
import json
from pathlib import Path
import runpy
from types import SimpleNamespace

import numpy as np

from collect import HERE, RUNS, plan

prior = SimpleNamespace(**runpy.run_path(str(RUNS/"terminal-feedback-routing/fit.py")))


def read(name):
    return json.loads((HERE/name).read_text())


def grade(case, spec):
    packets = {row["id"]: row for row in read("review-packets.json")}
    outputs = read("verification.json")["outputs"]
    marks = read("review.json")
    assert set(packets) == set(outputs) == set(marks) == set(spec["requests"])
    base = sum(x["points"] for x in case["public"])
    eligible = {tuple(row["requires"]): row["points"] for row in case["comparisons"]}
    graded = {}
    for key, mark in marks.items():
        packet = packets[key]
        out = outputs[key]
        text = out["text"]
        pair = tuple(spec["requests"][key]["pair"])
        sources = {row["id"]: row["text"] for row in packet["sources"]}
        assert set(pair) == set(sources)
        assert text == mark["span"] == packet["comparison"]
        assert mark["status"] in {"met", "clear", "none", "uncertain", "unsupported"}
        assert (mark["status"] == "none") == (text == "NONE")
        assert mark["reason"]
        assert set(mark["source_quotes"]) <= set(sources)
        assert all(quote and quote in sources[name] for name, quote in mark["source_quotes"].items())
        if mark["status"] == "met":
            assert pair in eligible and set(mark["source_quotes"]) == set(pair)
        points = eligible[pair] if mark["status"] == "met" else 0
        available = base + sum(source["points"] for source in packet["sources"])
        record = [x["text"] for x in case["public"]] + [sources[name] for name in pair]
        if text != "NONE":
            record.append(text)
        words = len(" ".join(record).split())
        structural = bool(text) and out["termination"] == "complete" and len(text.split()) <= 42
        assert len(" ".join(record[:4]).split()) <= case["word_cap"]
        clears = structural and words <= case["word_cap"] and mark["status"] not in {"uncertain", "unsupported"}
        released = available + points if clears else 0
        graded[key] = {
            "pair": list(pair), "order": spec["requests"][key]["order"], "status": mark["status"],
            "final_words": words, "raw_released": released,
            "screened": max(released, available), "source_only": available,
            "authored": available + eligible.get(pair, 0),
        }
    return graded


def worlds(case, graded):
    base = sum(x["points"] for x in case["public"])
    early = [row["id"] for row in case["delegate"]]
    late = [row["id"] for row in case["clause"]]
    values = {}
    for order in ("canonical", "reversed"):
        pairs = {tuple(row["pair"]): row for row in graded.values() if row["order"] == order}
        for metric in ("raw_released", "screened", "source_only", "authored"):
            if order == "reversed" and metric in {"source_only", "authored"}:
                continue
            values[f"{order}/{metric}"] = np.array(
                [base] + [base + b["points"] for b in case["delegate"]+case["clause"]]
                + [pairs[e, d][metric] for e, d in product(early, late)], dtype=float)
    return values


def held(tables, routes, spec):
    held_spec = spec["held"]
    rows = {}
    for name, table in tables.items():
        values = []
        for q0, q1, price, mass in product(held_spec["delivery"], held_spec["delivery"],
                                            held_spec["prices"], held_spec["priors"]):
            setting = q0, q1, price, np.array(mass)
            arms = {}
            for label, observed in (("arrival_only", np.ones(3, dtype=int)), ("peer", np.arange(1, 4))):
                for key, estimate in (("oracle", table), ("fixed_authored", tables["canonical/authored"]),
                                      ("fixed_source_only", tables["canonical/source_only"])):
                    decision = prior.best_route(estimate, observed, setting)
                    arms[f"{key}/{label}"] = prior.pay(table, observed, setting, *decision)
                if label in routes:
                    for count, checkpoint in routes[label].items():
                        decision = prior.frozen_route(checkpoint, observed, setting)
                        arms[f"fit_{count}/{label}"] = prior.pay(table, observed, setting, *decision)
            values.append({"setting": [q0, q1, price, mass],
                           "arms": {label: value.round(8).tolist() for label, value in arms.items()}})
        metrics = ("utility", "released", "send_cost", "released_target_comparison", "zero_release_pair")
        rows[name] = {
            "summary": {label: dict(zip(metrics, np.mean([row["arms"][label] for row in values],
                                                        axis=0).round(8).tolist(), strict=True))
                        for label in values[0]["arms"]},
            "rows": values,
        }
    return rows


def report():
    spec = read("plan.json")
    assert spec == plan()
    case = read("case.json")
    graded = grade(case, spec)
    tables = worlds(case, graded)
    training = prior.plan()
    training["observations"] = spec["training"]["checkpoints"]
    before = held(tables, {}, training)
    selected = before["canonical/screened"]["summary"]
    gain = selected["oracle/peer"]["utility"] - selected["oracle/arrival_only"]["utility"]
    fits = {}
    if gain > 1e-8:
        fits = {label: prior.train(tables["canonical/screened"], observed, training, True)
                for label, observed in (("arrival_only", np.ones(3, dtype=int)), ("peer", np.arange(1, 4)))}
    return {"grades": graded, "tables": {name: table.tolist() for name, table in tables.items()},
            "screened_canonical_peer_headroom": round(gain, 8),
            "fits": {name: {"checkpoints": row[0], "train_trace": row[1]} for name, row in fits.items()},
            "evaluation": held(tables, {label: row[0] for label, row in fits.items()}, training) if fits else before}


if __name__ == "__main__":
    print(json.dumps(report(), ensure_ascii=False, indent=2))
