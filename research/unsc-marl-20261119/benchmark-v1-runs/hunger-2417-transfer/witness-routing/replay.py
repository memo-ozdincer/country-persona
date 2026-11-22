"""Render witnessed comparisons and replay receipt-value routing."""
from collections import Counter
import json

import numpy as np

from select_witness import PARENT, REQUIRED, bind, evidence, key, plan, read, registry
import score as parent_score


def compare(case, requests, outputs):
    assert requests.keys() == outputs.keys()
    registered = registry()
    fixture = read("cards.json")
    original = {row["id"]: row for row in case["delegate"] + case["clause"]}
    refs = {tuple(p["requires"]): p for p in case["comparisons"]}
    grades = {}
    counters = Counter()
    for ident, item in requests.items():
        order, pair = item["order"], tuple(item["pair"])
        panels = json.loads(item["request"]["messages"][1]["content"])
        assert panels == evidence(fixture["cards"], pair, order)
        decision = bind(panels, outputs[ident], registered)
        support = decision["registered"]
        counters[f"{item['cohort']}/{decision['status']}"] += 1
        if decision["admitted"]:
            counters[f"{item['cohort']}/admitted"] += 1
        if decision["status"] == "linked" and decision["proposal"] != support:
            counters[f"{item['cohort']}/false_link"] += 1
        row = item | {"verdict": decision, "reply": outputs[ident]}
        if item["cohort"] == "historical":
            assert (support is not None) == (pair in refs)
            sources = case["public"] + [original[name] for name in pair]
            base = sum(s["points"] for s in sources)
            extra = refs[pair]["points"] if decision["admitted"] else 0
            texts = [s["text"] for s in sources]
            if extra:
                texts.append(refs[pair]["text"])
            record = "\n\n".join(texts)
            assert len(record.split()) <= case["word_cap"]
            row |= {"record": record, "screened": base+extra, "raw_released": base+extra,
                    "source_only": base, "authored": base+refs.get(pair, {"points": 0})["points"]}
        grades[ident] = row
    return grades, dict(sorted(counters.items()))


def mutation_audit(requests, outputs):
    registered = registry()
    checks = 0
    for ident, row in requests.items():
        panels = json.loads(row["request"]["messages"][1]["content"])
        kind = registered.get(key(panels))
        if kind is None:
            continue
        valid = {"text": json.dumps({"kind": kind, "spans": REQUIRED[kind]}), "termination": "complete"}
        assert bind(panels, valid, registered)["admitted"]
        for title, fields in panels.items():
            for span in fields:
                altered = {name: values.copy() for name, values in panels.items()}
                altered[title][span] += " [altered]"
                assert not bind(altered, valid, registered)["admitted"]
                checks += 1
        for rejected in (
            {"text": '{"kind":[],"spans":[]}', "termination": "complete"},
            {"text": '{"kind":"reporting_frequency","spans":["d2","p1","p1","p2"]}', "termination": "complete"},
            outputs[ident] | {"termination": "cap"},
        ):
            assert not bind(panels, rejected, registered)["admitted"]
            checks += 1
    return checks


def run():
    spec = read("plan.json")
    assert spec == plan()
    case = read("case.json", PARENT)
    outputs = read("verification.json")["outputs"]
    grades, counts = compare(case, spec["requests"], outputs)
    valid = {key: row for key, row in grades.items() if row["cohort"] == "historical"}
    tables = parent_score.worlds(case, valid)
    prior_reference = read("results.json", PARENT)["tables"]["canonical/authored"]
    assert tables["canonical/authored"].tolist() == prior_reference
    training = parent_score.prior.plan()
    training["observations"] = [64, 256, 1024]
    before = parent_score.held(tables, {}, training)
    selected = before["canonical/screened"]["summary"]
    headroom = selected["oracle/peer"]["utility"] - selected["oracle/arrival_only"]["utility"]
    fits = {}
    if headroom > 1e-8:
        for label, observed in (("arrival_only", np.ones(3, dtype=int)), ("peer", np.arange(1, 4))):
            fits[label] = parent_score.prior.train(tables["canonical/screened"], observed, training, True)
    report = parent_score.held(tables, {key: row[0] for key, row in fits.items()}, training) if fits else before
    return {"counts": counts, "reject_mutations": mutation_audit(spec["requests"], outputs),
            "grades": grades, "tables": {name: table.tolist() for name, table in tables.items()},
            "headroom": round(headroom, 8),
            "fits": {name: {"checkpoints": row[0], "train_trace": row[1]} for name, row in fits.items()},
            "evaluation": report}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
