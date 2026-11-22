"""Check the prompt-only decision rule and isolate chair choice errors."""
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from math import exp
from pathlib import Path
import re
import sys

import torch

import relay_compromise as ranked
from relay_compromise_audit import oracle

DESCRIPTION = re.compile(r"(\w+) is (acceptable|preferred|strongly preferred)")
GRADES = {"acceptable": 1, "preferred": 2, "strongly preferred": 3}


def view(text, names):
    delivered = "Delivered card. " in text
    cards = text.split("Delivered card. " if delivered else "Card absent. Its public possibilities are ", 1)[1]
    possibilities = []
    for card in cards.removesuffix(".").split(" / "):
        values = {name: GRADES[grade] for name, grade in DESCRIPTION.findall(card)}
        assert len(values) == len(card.split("; "))
        assert values.keys() <= set(names)
        possibilities.append(tuple(values.get(name, 0) for name in names))
    return delivered, possibilities


def route_replay(directory, scores):
    fitted = directory.parent / "relay-compromise/report.json"
    fit = json.loads(fitted.read_text())
    for name, digest in fit["source_hashes"].items():
        assert sha256((ranked.relay.HERE / name).read_bytes()).hexdigest() == digest
    delegate_policy = ranked.Policy()
    delegate_policy.load_state_dict({name: torch.tensor(value)
                                     for name, value in fit["training"]["optimality"]["weights"].items()})
    outcomes = {}
    torch.set_num_threads(1)
    with torch.no_grad():
        for name, task in ranked.fixtures().items():
            outcomes[name] = {}
            for channel in ("peer", "one_round", "mute_near", "mute_far", "mute_both"):
                rows = []
                for world in task.worlds:
                    # The original deterministic chair moves only after all deliveries.
                    transport = ranked.choose(task, "optimal", delegate_policy, world, channel)
                    left, right = ranked.delivered(transport)
                    score = scores[name, left, right]
                    rows.append({"world": world, "received": [left, right], **score,
                                 "completed_decision": score["warranted"] and score["choice"] != "unresolved",
                                 "transport": transport["deliveries"]})
                outcomes[name][channel] = rows
    return {"frozen_delegate_fit_sha256": sha256(fitted.read_bytes()).hexdigest(),
            "outcomes": outcomes}


def ceilings():
    reference = {}
    for name, task in ranked.fixtures().items():
        names = task.actions[:-1]
        results = {world: oracle(names, task.card(0, world[0]), task.card(1, world[1]))
                   for world in task.worlds}
        reference[name] = {}
        for condition, see_left, see_right in (("none", False, False), ("one_round", True, False),
                                               ("far_only", False, True), ("both", True, True)):
            by_view = {}
            for (left, right), decisions in results.items():
                key = (left if see_left else None, right if see_right else None)
                by_view.setdefault(key, []).append(decisions)
            best = sum(max(Counter(choice for decisions in group for choice in decisions).values())
                       for group in by_view.values())
            grounded = sum(len(group) for group in by_view.values() if set.intersection(*group))
            reference[name][condition] = {"correct_upper_bound": best, "certifiable": grounded,
                                          "worlds": len(results)}
    return reference


def audit(directory):
    report = json.loads((directory / "report.json").read_text())
    expected = {(family, *row["visible_cards"]): row for family, arms in report["groups"].items()
                for rows in arms.values() for row in rows}
    source = directory / "actions.jsonl"
    counters = Counter()
    errors = []
    diagnostic = {}
    for line in source.read_text().splitlines():
        row = json.loads(line)
        family, phase, left, right, _ = row["observation"]
        assert phase == 3
        _, relay, far, *choices = row["messages"][-1]["content"].splitlines()
        labels, menu = zip(*(choice.split(". ", 1) for choice in choices), strict=True)
        assert labels == tuple("ABCDEFGHI"[:len(menu)]) and menu[-2:] == ("impasse", "unresolved")
        names = menu[:-2]
        left_seen, left_cards = view(relay, names)
        right_seen, right_cards = view(far, names)
        assert (left_seen, right_seen) == (bool(left), bool(right))
        eligible = set.intersection(*(oracle(names, a, b) for a, b in product(left_cards, right_cards)))
        gold = eligible or {"unresolved"}
        record = expected.pop((family, left, right))
        assert set(record["warranted_choices"]) == gold
        choice = menu[max(range(len(menu)), key=row["scores"].__getitem__)]
        assert record["choice"] == choice and record["pass"] == (choice in gold)
        condition = record.get("scenario", "partial")
        counters[family, condition, "observations"] += 1
        counters[family, condition, "model_pass"] += choice in gold
        top = max(row["scores"])
        mass = [exp(value - top) for value in row["scores"]]
        counters[family, condition, "restricted_success_sum"] += (
            sum(weight for option, weight in zip(menu, mass, strict=True) if option in gold) / sum(mass)
        )
        literal_label = labels[menu.index(choice)]
        if condition == "agreement" and literal_label in gold:
            counters[family, condition, "answer_letter_equals_best_package_id"] += 1
        if condition == "agreement":
            feasible = set(record["feasible_options"])
            filtered = max(feasible, key=lambda option: row["scores"][menu.index(option)])
            counters[family, condition, "model_pass_after_feasibility_filter"] += filtered in gold
            counters[family, condition, "model_feasible"] += choice in feasible
        diagnostic[family, left, right] = {"choice": choice, "warranted": choice in gold}
        if choice not in gold:
            errors.append({"family": family, "visible_cards": [left, right], "model_choice": choice,
                           "warranted_choices": sorted(gold), "condition": condition})
    assert not expected
    counts = {}
    for (family, condition, metric), value in sorted(counters.items()):
        counts.setdefault(family, {}).setdefault(condition, {})[metric] = value
    return {"prompt_rule_checks": report["observations"], "actions_sha256": sha256(source.read_bytes()).hexdigest(),
            "counts": counts, "errors": errors, "visibility_ceilings": ceilings(),
            "hybrid": route_replay(directory, diagnostic)}


if __name__ == "__main__":
    print(json.dumps(audit(Path(sys.argv[1])), indent=2))
