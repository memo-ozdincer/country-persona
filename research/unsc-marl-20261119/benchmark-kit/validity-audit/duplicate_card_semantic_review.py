"""Evaluate semantic card grounding, then replay the routing policies."""
import argparse
from collections import Counter, defaultdict
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

import numpy as np

STRESSES = {"complete_or_missing": ("full", "missing"),
            "reordered_or_reversed": ("reordered", "reversed")}
READERS = ("oracle", "position_only", "mention_only", "first_rotation", "pooled", "all_orders_agree")
EVIDENCE = Path(__file__).resolve().parent.parent / "evidence/duplicate-card-routes"
PRIVATE = tuple(product(range(4), repeat=2))
MASKS = tuple(product(range(2), repeat=2))
FAULTS = {"none": (0., 0.), "both_10": (.1, .1), "both_25": (.25, .25)}
RECEIPT = np.bitwise_or.outer([0, 1, 2], [0, 1, 2])
SIGNAL_COST = .05
MESSAGE_COST = .2


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def mask_weight(mask, failure):
    return np.prod([1 - failure if kept else failure for kept in mask])


def read_all(directory):
    lock = json.loads((EVIDENCE / "semantic-lock.json").read_text())
    source = directory / "actions.jsonl"
    complete = json.loads((directory / "complete.json").read_text())
    launch = json.loads((directory / "launch.json").read_text())
    assert complete["sha256"] == digest(source) and launch["sha256"] == lock["sha256"]
    root = Path(__file__).resolve().parents[2]
    assert all(digest(root / path) == value for path, value in lock["sha256"].items())
    rows = {tuple(r["observation"]): r for r in map(json.loads, source.read_text().splitlines())}
    assert len(rows) == complete["records"] == len(lock["prompts"])
    orders = {}
    for prompt in lock["prompts"]:
        key = tuple(prompt["observation"])
        row = rows[key]
        assert row["legal"] == prompt["legal"] and row["messages"] == prompt["messages"]
        orders[key] = row["legal"]
    readings = {}
    for case, source_id, variant, _, truth in lock["key"]:
        decisions, probs = [], []
        for i in range(3):
            key = (case, source_id, variant, i)
            order, row = orders[key], rows[key]
            logits = np.asarray(row["scores"], dtype=float)
            assert np.isfinite(logits).all()
            mass = np.exp(logits - logits.max())
            mass /= mass.sum()
            probs.append(mass[np.argsort(order)])
            decisions.append(order[int(logits.argmax())])
        readings[case, source_id, variant] = {
            "truth": truth, "decisions": decisions, "first_rotation": decisions[0],
            "pooled": int(np.mean(probs, axis=0).argmax()),
            "all_orders_agree": decisions[0] if len(set(decisions)) == 1 else 0,
            "order_disagreement": len(set(decisions)) > 1,
        }
    return readings, rows


def shelf(case, inventory, facing, style, reader, readings):
    available = {}
    for position, kind in enumerate((2, 1) if facing else (1, 2), 1):
        variant = style[0] if inventory & kind else style[1]
        row = readings[case, kind, variant]
        actual = row["truth"]
        if reader == "oracle":
            predicted = actual
        elif reader == "position_only":
            predicted = position
        elif reader == "mention_only":
            predicted = kind
        else:
            predicted = row[reader]
        if predicted:
            available.setdefault(predicted, actual)
    return sum(available), available


def simulate(case, prior, reward, table, rate, style, reader, readings):
    signal_fail, card_fail = rate
    signal_count = delivery_count = rejected = false_announce = valid_pair = 0.
    for inventories, world_weight in zip(PRIVATE, prior, strict=True):
        for order in MASKS:
            views = [shelf(case, value, order[seat], style, reader, readings)
                     for seat, value in enumerate(inventories)]
            predicted, catalogs = zip(*views, strict=True)
            bits = tuple(int(table[seat, p, 0]) for seat, p in enumerate(predicted))
            weight = world_weight / len(MASKS)
            signal_count += weight * sum(bits)
            false_announce += weight * int(any(bit and not inv & 2 for bit, inv in zip(bits, inventories, strict=True)))
            for link in MASKS:
                mass = weight * mask_weight(link, signal_fail)
                actions = tuple(int(table[seat, p, 1 + 2 * bits[seat] + bits[1-seat] * link[seat]])
                                for seat, p in enumerate(predicted))
                delivery_count += mass * sum(bool(action) for action in actions)
                invalid = [bool(a) and catalogs[seat].get(a) != a for seat, a in enumerate(actions)]
                rejected += mass * int(any(invalid))
                surviving = tuple(0 if wrong else action for action, wrong in zip(actions, invalid, strict=True))
                if RECEIPT[surviving] == 3:
                    valid_pair += mass * (1 - card_fail) ** 2
    net = reward[0, 0] + (reward[1, 2] - reward[0, 0]) * valid_pair
    return {"net": float(net - SIGNAL_COST * signal_count - MESSAGE_COST * delivery_count),
            "both_attested_cards": float(valid_pair), "announcements_attempted": float(signal_count),
            "deliveries_attempted": float(delivery_count),
            "false_announcement_probability": float(false_announce),
            "one_or_more_unsupported_deliveries_attempted": float(rejected)}


def exact_silent(prior, gain, card_fail):
    # Independently enumerate the feasible inventory-to-action maps.
    policies = list(product((0,), (0, 1), (0, 2), (0, 1, 2)))
    best = float("-inf")
    for left, right in product(policies, repeat=2):
        value = 0.
        for (a, b), mass in zip(PRIVATE, prior, strict=True):
            x, y = left[a], right[b]
            value += mass * (gain * (1 - card_fail) ** 2 * (RECEIPT[x, y] == 3)
                             - MESSAGE_COST * (bool(x) + bool(y)))
        if value > best + 1e-10:
            best = value
            optimum = (left, right)
    table = np.zeros((2, 4, 5), dtype=int)
    table[:, :, 1:] = np.asarray(optimum)[:, :, None]
    return best, table


def best_silent_through_reader(case, prior, gain, card_fail, style, reader, readings):
    views = defaultdict(float)
    for (left, right), probability in zip(PRIVATE, prior, strict=True):
        for facing in MASKS:
            a, l = shelf(case, left, facing[0], style, reader, readings)
            b, r = shelf(case, right, facing[1], style, reader, readings)
            views[a, b, l.get(1, 0) == 1, l.get(2, 0) == 2, r.get(1, 0) == 1, r.get(2, 0) == 2] += probability / 4
    policies = np.array(list(product((0,), (0, 1), (0, 2), (0, 1, 2))))
    scores = np.zeros((len(policies), len(policies)))
    for (a, b, l1, l2, r1, r2), mass in views.items():
        x, y = policies[:, a, None], policies[None, :, b]
        distinct = ((x == 1) & (y == 2) & l1 & r2) | ((x == 2) & (y == 1) & l2 & r1)
        costs = MESSAGE_COST * ((x != 0).astype(int) + (y != 0))
        scores += mass * (gain * (1 - card_fail) ** 2 * distinct - costs)
    left, right = np.unravel_index(scores.argmax(), scores.shape)
    table = np.zeros((2, 4, 5), dtype=int)
    table[:, :, 1:] = policies[[left, right], :, None]
    return float(scores[left, right]), table


def reward_tables():
    venezuela = json.loads((EVIDENCE / "writer/scores.json").read_text())
    dprk = json.loads((EVIDENCE / "dprk-qualification/scores.json").read_text())
    v = {r["id"].split("/")[-2]: r["floor"] for r in venezuela["packet_scores"]
         if r["critical_guard"] == "clear" and r["under_limit"] and r["ended"]}
    d = {tuple(r["received"]): r["authored_plus_reviewed_points"]
         for r in dprk["source_order_diagnostic"]["four_records"]}
    return {
        "venezuela": np.array([v["public"], 0, 0, v["CHAIR-INDONESIA"]])[RECEIPT],
        "dprk": np.array([d[()], d["JAPAN",], d["CHINA",], d["JAPAN", "CHINA"]])[RECEIPT],
    }


def report(directory):
    readings, rows = read_all(directory)
    archive = json.loads((EVIDENCE / "buffered-fit.json").read_text())
    trained = np.array(archive["trained_tables"]["matched"])
    routes = json.loads((EVIDENCE / "dprk-routes.json").read_text())
    priors = {name: [r["probability"] for r in values["silent"]["worlds"]]
              for name, values in routes["arms"].items()}
    matrices = reward_tables()
    results = {}
    for case, reward in matrices.items():
        per_case = {key: value for key, value in readings.items() if key[0] == case}
        totals = {}
        for reader in ("first_rotation", "pooled", "all_orders_agree"):
            counts = Counter()
            for (_, _, variant), x in per_case.items():
                truth, found = x["truth"], x[reader]
                counts[f"{variant}_correct"] += int(truth == found)
                counts["false_full_claims"] += int(found != 0 and truth != found)
                counts["missed_complete_claims"] += int(truth != 0 and found != truth)
            totals[reader] = counts
        evaluations = {}
        for tilting, prior in priors.items():
            evaluations[tilting] = {}
            for loss in ("none", "both_10", "both_25"):
                rates = FAULTS[loss]
                gain = reward[1, 2] - reward[0, 0]
                assert gain == 14
                best_silent, silent = exact_silent(prior, gain, rates[1])
                control = archive["priors"][tilting][loss]
                assert np.isclose(best_silent + 35, control["exact_buffered_silent"]["net"])
                views = {}
                for style_name, style in STRESSES.items():
                    masks = {}
                    for reader in READERS:
                        masks[reader] = {
                            name: simulate(case, prior, reward, table, rates, style, reader, readings)
                            for name, table in (("trained", trained), ("silent", silent))
                        }
                        if reader in ("oracle", "pooled"):
                            bound, adapted = best_silent_through_reader(case, prior, gain, rates[1], style, reader, readings)
                            fair = simulate(case, prior, reward, adapted, rates, style, reader, readings)
                            assert np.isclose(fair["net"], bound + reward[0, 0])
                            assert fair["net"] >= masks[reader]["silent"]["net"] - 1e-9
                            masks[reader]["silent_optimized_for_reader"] = fair
                    assert np.isclose(masks["oracle"]["silent"]["net"], best_silent + reward[0, 0])
                    assert np.isclose(masks["oracle"]["trained"]["net"] - reward[0, 0] + 35,
                                      control["matched_fit"]["net"])
                    views[style_name] = masks
                evaluations[tilting][loss] = views
        case_rows = [row for row in rows.values() if row["observation"][0] == case]
        results[case] = {"total_passages": len(per_case),
                         "passages_with_order_disagreement": sum(row["order_disagreement"] for row in per_case.values()),
                         "mean_menu_probability": sum(row["legal_mass"] for row in case_rows) / len(case_rows),
                         "reader_accuracy": totals, "evaluations": evaluations}
    return {
        "scope": "Closed-source capability classification of authored complete, missing and counterfactual passages; "
                 "exact replay with canonicalization of attested complete cards and a buffered archived writer.",
        "actions_sha256": sha256((directory / "actions.jsonl").read_bytes()).hexdigest(),
        "observation_count": len(rows),
        "passage_readings": [{"key": key, **value} for key, value in readings.items()],
        "results": results,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(report(args.directory), indent=2))
