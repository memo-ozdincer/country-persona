"""Audit the frozen compromise policy and the decision rubric independently."""
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import sys

import torch

import relay_compromise as experiment


def oracle(options, left, right):
    shortlist = [i for i, (a, b) in enumerate(zip(left, right, strict=True)) if a > 0 and b > 0]
    if not shortlist:
        return {"impasse"}
    floor = max(min(left[i], right[i]) for i in shortlist)
    protected = [i for i in shortlist if left[i] >= floor and right[i] >= floor]
    total = max(left[i] + right[i] for i in protected)
    return {options[i] for i in protected if left[i] + right[i] == total}


def check_record(task, row):
    left_id, right_id = row["world"]
    first, second, final = row["deliveries"]
    assert first["owner"] == "far delegate" and second["owner"] == "relay"
    assert first["intended_mask"] in (0, right_id) and second["intended_mask"] in (0, left_id)
    for delivery in row["deliveries"]:
        assert delivery["delivered_mask"] in (0, delivery["intended_mask"])
    if final["owner"] == "far delegate":
        assert final["intended_mask"] == first["delivered_mask"]
        left_id_visible, right_id_visible = second["delivered_mask"], final["delivered_mask"]
    else:
        assert final["owner"] == "relay" and final["intended_mask"] in (0, left_id)
        left_id_visible = second["delivered_mask"] or final["delivered_mask"]
        right_id_visible = 0
    left = (task.card(0, left_id_visible),) if left_id_visible else task.cards[0]
    right = (task.card(1, right_id_visible),) if right_id_visible else task.cards[1]
    names = task.actions[:-1]
    possible = set.intersection(*(oracle(names, a, b) for a, b in product(left, right)))
    actual = oracle(names, task.card(0, left_id), task.card(1, right_id))
    assert row["warranted_optimal"] == (row["choice"] in possible)
    assert row["optimal"] == (row["choice"] in actual)
    assert {task.actions[i] for i in row["visible_optimal_options"]} == possible
    assert {task.actions[i] for i in row["optimal_options"]} == actual


def audit(path):
    torch.set_num_threads(1)
    report = json.loads(path.read_text())
    for name, digest in report["source_hashes"].items():
        assert sha256((experiment.relay.HERE / name).read_bytes()).hexdigest() == digest
    policy = experiment.Policy()
    policy.load_state_dict({k: torch.tensor(value)
                            for k, value in report["training"]["optimality"]["weights"].items()})
    panels = {}
    audited = 0
    with torch.no_grad():
        for name, original in experiment.fixtures().items():
            package_names = original.actions[:-1]
            metrics, failures = Counter(), []
            for family_results in report["results"].values():
                for rows in family_results[name].values():
                    for world, row in zip(original.worlds, rows, strict=True):
                        assert tuple(row["world"]) == world
                        check_record(original, row)
                        audited += 1
            for shift, swapped in product(range(len(package_names)), (False, True)):
                indices = tuple((i + shift) % len(package_names) for i in range(len(package_names)))
                names = tuple(package_names[i] for i in indices)
                cards = tuple(tuple(tuple(card[i] for i in indices) for card in seat)
                              for seat in original.cards[::(-1 if swapped else 1)])
                task = experiment.workshop(name, names, cards)
                for world in task.worlds:
                    row = experiment.choose(task, policy, policy, world, "peer")
                    check_record(task, row)
                    left, right = (task.card(role, code) for role, code in enumerate(world))
                    acceptable = oracle(names, left, right)
                    assert acceptable == {task.actions[i] for i in row["optimal_options"]}
                    group = "unchanged" if not swapped and shift == 0 else "swapped" if swapped else "rotated"
                    metrics[group, "worlds"] += 1
                    metrics[group, "warranted"] += row["warranted_optimal"]
                    if row["choice"] not in acceptable or not row["warranted_optimal"]:
                        failures.append({"shift": shift, "swapped": swapped, "world": world,
                                         "choice": row["choice"], "acceptable": sorted(acceptable)})
            panels[name] = {"counts": {group: {key: metrics[group, key] for key in ("worlds", "warranted")}
                                       for group in ("unchanged", "rotated", "swapped")},
                            "failures": failures}
    return {"report_sha256": sha256(path.read_bytes()).hexdigest(),
            "record_checks": audited, "panels": panels}


if __name__ == "__main__":
    print(json.dumps(audit(Path(sys.argv[1])), indent=2))
