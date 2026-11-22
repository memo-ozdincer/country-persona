"""Replay cross-decoder role assignments without changing source records."""
import json
from itertools import product
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def evaluate(records, p, action, third):
    return sum(availability * p ** mask.bit_count() * (1 - p) ** (3 - mask.bit_count())
               * records[f"{action[early + 1 if mask & 2 else 0]}{early}{third}"][mask]["score"]["released_70"]
               for (early, availability), mask in product(enumerate((.75, .25)), range(8)))


def run():
    reference = read(HERE.parent.parent / "results.json")["orders"]
    older = read(HERE.parent / "scores.json")["scenarios"]
    verified = read(HERE / "scores.json")["modes"]
    current = verified["wire"]["scenarios"]
    targeted = verified["forecast"]["scenarios"]
    rows = []
    for before, after, intervention in zip(older, current, targeted, strict=True):
        order, p = before["order"], before["receipt"]
        records = reference[order]["records"]
        assert (order, p) == (after["order"], after["receipt"]) == (intervention["order"], intervention["receipt"])
        atom, wire = [r["results"]["content"]["mean"] for r in (before, after)]
        scores = {"atomic_later_atomic_independent": evaluate(records, p, atom["later_by_view"], atom["third"]),
                  "wire_later_atomic_independent": evaluate(records, p, wire["later_by_view"], atom["third"]),
                  "atomic_later_wire_independent": evaluate(records, p, atom["later_by_view"], wire["third"]),
                  "wire_later_wire_independent": evaluate(records, p, wire["later_by_view"], wire["third"])}
        assert abs(scores["atomic_later_atomic_independent"] - atom["released"]) < 1e-9
        assert abs(scores["wire_later_wire_independent"] - wire["released"]) < 1e-9
        result = {"order": order, "receipt": p, "scores": scores}
        if (order, p) == ("uk_later", .95):
            revised = intervention["results"]["content"]["mean"]
            result["forecast_effect_by_executed_third"] = {
                str(decision + 1): evaluate(records, p, revised["later_by_view"], decision) -
                evaluate(records, p, wire["later_by_view"], decision)
                for decision in (0, 1)}
        rows.append(result)
    return {"mean": {arm: mean(row["scores"][arm] for row in rows) for arm in rows[0]["scores"]},
            "rows": rows, "status": "Post-result component substitution holding recorded policy tables fixed."}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
