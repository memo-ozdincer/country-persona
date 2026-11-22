"""Fit against the public rubric scale and replay the same final-record branches."""
from hashlib import sha256
import sys
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import calibrate as training

sys.path.insert(0, str(HERE))
import replay as r

env, value = r.env, r.value
RATES = (.20, .55, .69, .70, .71, .80)


def criterion_weight():
    weights = {unit["weight"] for case in r.e.cases().values() if case["track"] == "workshop"
               for unit in case["rubric"] if unit["id"] == "positions"}
    assert len(weights) == 1
    return weights.pop() / 70.


def run():
    train, _ = training.train_and_held()
    bonus = criterion_weight()
    with patch.object(env, "BONUS", bonus):
        fitted, residual, count = value.fit(train)

    marks = r.e.read(HERE / "marks.json")
    original = r.score(r.replay(rates=RATES), marks)
    revised = r.score(r.replay(rates=RATES, value_heads=fitted), marks)
    table = {}
    for rate in RATES:
        before = original["rates"][str(rate)]["arms"]
        after = revised["rates"][str(rate)]["arms"]
        assert before["no_followup"] == after["no_followup"] and before["joint"] == after["joint"]
        table[str(rate)] = {"silence": before["no_followup"], "proxy_value": before["value"],
                            "rubric_value": after["value"]}
    files = (Path(__file__), HERE/"reweight-protocol.md", HERE/"replay.py", HERE/"render.py",
             HERE/"scores.json", HERE/"marks.json", HERE.parent/"value-fit.json")
    return {"credit_per_completed_mandate_item": bonus, "heads": fitted, "training_rows_per_head": count,
            "fit_residual": residual, "results": table,
            "sha256": {str(p.relative_to(env.CHAIR.ROOT)): sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    r.e.emit(run())
