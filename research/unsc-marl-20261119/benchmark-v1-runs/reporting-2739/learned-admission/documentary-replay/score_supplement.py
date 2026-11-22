"""Score the completed record replay with two new frozen-reader probes."""
from itertools import product
from pathlib import Path
from statistics import mean

import supplement as study

doc, e, HERE = study.doc, study.e, study.HERE
TARGET = "algeria-full-rationale"


def score(text, statements, registry, gold):
    result = doc.judge(text, statements, registry, gold)
    if TARGET in statements:
        verdict = result["verdict"]
        unit, = [u for u in verdict["units"] if u["id"] == "algeria-reason"]
        unit.update(status="met", response=statements[TARGET],
                    source=[{"block": "algeria", "quote": registry[TARGET]["witness"]}],
                    reason="Identifies the implementation objection and the concern about using self-defence against sovereign territory.")
        result["score"] = e.final_score(doc.CASE, [{}, {}, {"text": text, "termination": "complete"}], verdict)
    return result


def run():
    before = e.read(HERE / "results.json")
    assert before == doc.benchmark()
    pool = [*e.read(doc.ADMISSION / "held.json"), *study.ROWS]
    registry = {row["id"]: {k: v for k, v in row.items() if k != "expected"} for row in pool}
    gold = {row["id"]: row["expected"] for row in pool}
    receipt = e.read(HERE / "supplement-verified.json")
    calls = study.OUT / "calls.jsonl"
    assert doc.hash_bytes(calls) == receipt["evidence_sha256"]["calls.jsonl"]
    views = doc.team.observations(calls, "supplement")
    assert set(views) == {r["id"] for r in study.ROWS}
    weights = e.read(doc.ADMISSION / "fit.json")["frozen"]
    rows, fresh = {}, {}
    for order in (0, 1):
        new_labels = {key: doc.admissions(value, weights, order) for key, value in views.items()}
        fresh[str(order)] = new_labels
        admitted = before["decisions_before_delivery"][str(order)] | new_labels
        for arm, mask in product(doc.POLICIES, range(4)):
            choices = [key for key in registry if (gold[key] if arm == "privileged_semantic" else
                                                   admitted[key][arm]) == "supports"]
            text, actual = doc.publish(choices, registry, mask)
            key = f"{order}/{arm}/{mask}"
            outcome = score(text, actual, registry, gold)
            rows[key] = outcome | {"record": text, "admitted": list(actual),
                                   "released_delta": outcome["score"]["released_70"] -
                                   before["records"][key]["score"]["released_70"]}
    ids = tuple((order, mask) for order, mask in product((0, 1), range(4)))
    means = {}
    for arm in doc.POLICIES:
        conditions = [rows[f"{order}/{arm}/{mask}"] for order, mask in ids]
        full = [rows[f"{order}/{arm}/3"]["score"]["released_70"] for order in (0, 1)]
        means[arm] = {"full_receipt_released": full,
                      "uniform_receipt_released": mean(r["score"]["released_70"] for r in conditions),
                      "guard_failures": sum(bool(r["unsupported_assertions"]) for r in conditions),
                      "strict_full_receipt": sum(v == 70 for v in full)}
    assert len(rows) == 40
    pins = [Path(__file__), HERE / "results.json", HERE / "supplement-plan.json", HERE / "supplement-verified.json"]
    return {"new_relations": fresh, "means": means, "records": rows,
            "sha256": {path.name: doc.hash_bytes(path) for path in pins}}


if __name__ == "__main__":
    e.emit(run())
