"""Replay the case with procedural evidence compiled from the public packet."""
from itertools import product
from pathlib import Path
from statistics import mean

import score_records as study

HERE, e, CASE, run = study.HERE, study.e, study.CASE, study.run


def inspect():
    baseline = e.read(HERE / "results.json")
    assert baseline == study.run_all()
    fixtures = run.fixtures()
    gold = {row["id"]: row["expected"] for row in fixtures}
    registry = {row["id"]: {k: v for k, v in row.items() if k != "expected"} for row in fixtures}
    chair = registry["chair-role"]
    public = e.judge.by_id(CASE["public"])
    assert chair["source"] in public
    assert chair["witness"] == public[chair["source"]]["text"]
    chair["owner"] = 4
    new, old, changes = {}, {}, []
    for order, arm, mask in product((0, 1), study.POLICIES, range(4)):
        key = f"{order}/{arm}/{mask}"
        admitted = baseline["records"][key]["admitted"]
        selected = [k for k in registry if k in admitted or k == "chair-role"]
        result = study.record(selected, mask | 4, registry, gold)
        previous = baseline["records"][key]
        assert set(result["admitted"]) == set(admitted) | {"chair-role"}
        assert result["false_assertions"] == previous["false_assertions"]
        assert result["score"]["units"]["role"] == "met"
        new[key], old[key] = result, previous["score"]["released_70"]
        if result["score"]["released_70"] != old[key]:
            changes.append(key)
    values = run.team.observations(run.OUT / "calls.jsonl", "held")
    fitted = e.read(run.FIT / "fit.json")["frozen"]
    reports = {}
    for row in fixtures:
        key = row["id"]
        reports[key] = run.team.measure((key, CASE["family"],
                            run.team.LABELS.index(row["expected"]), values[key]), fitted)
    for order in (0, 1):
        for label in ("chair-role", "india-voted-yes", "india-opposed-asean"):
            report = reports[label]["orders"][str(order)]
            for arm in ("fitted_greedy", "consensus"):
                expected = baseline["admission_labels"][str(order)][label][arm]
                score = report["policies"][arm]
                assert bool(score["true_admission"] + score["wrong_admission"]) == (expected != "unknown")
    summary = {}
    for arm in study.POLICIES:
        keys = [f"{order}/{arm}/{mask}" for order, mask in product((0, 1), range(4))]
        summary[arm] = {
            "full_receipt": [new[f"{order}/{arm}/3"]["score"]["released_70"] for order in (0, 1)],
            "uniform_receipt_mean": mean(new[key]["score"]["released_70"] for key in keys),
            "guard_failures": sum(new[key]["score"]["guard"] == "failed" for key in keys),
        }
    return {"scope": "Post hoc direct compilation of procedural facts from the existing public block.",
            "summary": summary, "changed_releases": changes, "records": new,
            "gate_readout": reports,
            "sha256": {p.name: run.team.pin(p) for p in (Path(__file__), HERE / "results.json")}}


if __name__ == "__main__":
    e.emit(inspect())
