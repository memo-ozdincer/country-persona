"""Cross evidence selection and dispatch without changing receipt probabilities."""
from statistics import mean

from context_test import HERE, PARENT, READ, frozen, prior


def run():
    result_path = HERE / "scores.json"
    base_path = PARENT / "routing.json"
    fitted = READ(result_path)["results"]
    route = READ(base_path)
    initial_id = route["condition_aliases"]["normal/native"]
    initial = route["results"][initial_id]
    sums = {}
    for name, scenario in fitted.items():
        selected_id = scenario["reused_route"]
        selected = route["results"][selected_id]
        start, end = route["banks"][initial_id], route["banks"][selected_id]
        rows = []
        for before, after in zip(initial["rows"], selected["rows"], strict=True):
            condition = {key: before[key] for key in ("law", "information", "review_offset")}
            assert all(after[k] == val for k, val in condition.items())
            a, b = before["receipts"]["nominal"], after["receipts"]["nominal"]
            assert abs(sum(a) - 1.) <= 1e-9 and abs(sum(b) - 1.) <= 1e-9
            projection = sum(p * y for p, y in zip(a, end, strict=True))
            source = before["outcomes"]["nominal"]
            dest = after["outcomes"]["nominal"]
            assert abs(sum(p * y for p, y in zip(a, start, strict=True)) - source["released"]) <= 1e-9
            assert abs(sum(p * y for p, y in zip(b, end, strict=True)) - dest["released"]) <= 1e-9
            rows.append(condition | {"input_change_on_frozen_route": projection - source["released"],
                        "routing_change_on_selected_bank": dest["released"] - projection,
                        "complete_released_change": dest["released"] - source["released"],
                        "complete_net_change_before_context_cost": dest["net"] - source["net"],
                        "prior_france_receipt_probability": sum(p for i, p in enumerate(a) if i & 1),
                        "replanned_france_receipt_probability": sum(p for i, p in enumerate(b) if i & 1)})
        metrics = ("input_change_on_frozen_route", "routing_change_on_selected_bank", "complete_released_change",
                   "complete_net_change_before_context_cost", "prior_france_receipt_probability", "replanned_france_receipt_probability")
        sums[name] = {"rows": rows, "mean": {key: mean(r[key] for r in rows) for key in metrics}}
    return {"result": sums, "sha256": {str(p.relative_to(prior.STUDY)): prior.digest(p)
                                       for p in (result_path, base_path)}}


if __name__ == "__main__":
    frozen.emit(run())
