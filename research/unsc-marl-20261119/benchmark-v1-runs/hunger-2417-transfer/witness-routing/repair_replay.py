"""Complete an incomplete witness list only for an exact registered packet."""
import json
from pathlib import Path
import runpy
from types import SimpleNamespace

import numpy as np

from select_witness import REQUIRED, bind, key, read, registry
replay = SimpleNamespace(**runpy.run_path(str(Path(__file__).with_name("replay.py"))))


def complete(panels, reply, registered):
    strict = bind(panels, reply, registered)
    kind = strict["proposal"]
    if strict["status"] != "invalid_witnesses" or kind != registered.get(key(panels)):
        return reply, []
    provided = json.loads(reply["text"])["spans"]
    unique = set(provided)
    required = set(REQUIRED[kind])
    covered_source = {span[0] for span in unique if span}
    if (len(unique) != len(provided) or not unique < required or covered_source != {"d", "p"}):
        return reply, []
    supplemented = sorted(required - unique)
    replacement = reply | {
        "text": json.dumps({"kind": kind, "spans": REQUIRED[kind]}),
    }
    assert bind(panels, replacement, registered)["admitted"]
    return replacement, supplemented


def run():
    before = read("results.json")
    spec = read("plan.json")
    outputs = read("verification.json")["outputs"]
    reg = registry()
    completed, changes, resolved = {}, {}, {}
    for ident, packet in spec["requests"].items():
        panels = json.loads(packet["request"]["messages"][1]["content"])
        completed[ident], added = complete(panels, outputs[ident], reg)
        strict = bind(panels, outputs[ident], reg)
        decision = bind(panels, completed[ident], reg)
        assert strict["admitted"] <= decision["admitted"]
        resolved[ident] = decision
        if added:
            changes[ident] = {"pair": packet["pair"], "order": packet["order"],
                              "original": outputs[ident]["text"], "supplied": added}
    case = read("case.json", replay.PARENT)
    graded, _ = replay.compare(case, spec["requests"], completed)
    history = {i:g for i,g in graded.items() if g["cohort"] == "historical"}
    tables = replay.parent_score.worlds(case, history)
    assert tables["canonical/authored"].tolist() == before["tables"]["canonical/authored"]
    canonical = tables["canonical/screened"]
    assert canonical.tolist() == tables["reversed/screened"].tolist()
    training = replay.parent_score.prior.plan()
    training["observations"] = [64, 256, 1024]
    traces = {}
    for label, tags in (("arrival_only", np.ones(3, dtype=int)), ("peer", np.arange(1, 4))):
        traces[label] = replay.parent_score.prior.train(canonical, tags, training, True)
    tables.update({f"strict/{order}": np.array(before["tables"][f"{order}/screened"])
                   for order in ("canonical", "reversed")})
    eval_rows = replay.parent_score.held(tables, {label: row[0] for label, row in traces.items()}, training)
    return {"repairs": changes, "decisions": resolved,
            "historical_records": {key: row["record"] for key, row in history.items()},
            "tables": {name: table.tolist() for name, table in tables.items()},
            "evaluation": eval_rows,
            "fits": {name: {"checkpoints": row[0], "train_trace": row[1]} for name, row in traces.items()}}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
