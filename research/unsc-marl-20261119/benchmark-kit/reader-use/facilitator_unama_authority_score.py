"""Assemble and score Council records, then replay the frozen two-desk request policy."""
import argparse
from itertools import permutations
import json
from pathlib import Path
import re

import numpy as np

import facilitator_unama_authority as study
import source_request_policy as route

WEIGHTS = {"decision": 14, "mandate": 14, "reporting": 6}
GUARDS = ("citation", "authority", "support")
LOSS = .10
LEAD = re.compile(r"^\[?(S[234])\]?\s*:?\s+(.*)$")


def public_record(source):
    return "\n".join(f"[{sid}] {text}" for sid, text in source["public"].items())


def normalize_leads(supplement, visible, fields):
    lines = []
    for line in supplement.splitlines():
        found = LEAD.fullmatch(line.strip())
        if found and found[1] in visible:
            sid, text = found.groups()
            if text.startswith(("supported ", "explained ")):
                text = f"{fields[sid]['speaker']} {text}"
            line = f"[{sid}] {text}"
        lines.append(line)
    return "\n".join(lines)


def views(directory):
    rows = study.verify(directory)
    source = study.packet()
    public = public_record(source)
    records = {}
    for mask in range(8):
        row = rows.get(f"bound/{mask}")
        supplement = row["output"] if row is not None else ""
        visible = study.selected(mask, source)
        for arm, body in (("bound", supplement), ("normalized", normalize_leads(supplement, visible, source["cards"]))):
            records[f"{arm}/{mask}"] = {
                "record": f"{public}\n{body}".strip(), "ended": row is None or row["ended"],
                "available": source["public"] | visible,
            }
    for mask in (0, 7):
        row = rows[f"raw/{mask}"]
        records[f"raw/{mask}"] = {
            "record": row["output"], "ended": row["ended"],
            "available": source["public"] | study.selected(mask, source),
        }
    return records


def score_record(value, marks):
    fields = {**WEIGHTS, **{f"{sid}.{unit}": 4 for sid in study.packet()["cards"] for unit in range(1, 4)}}
    assert marks.keys() == fields.keys() | set(GUARDS)
    text = value["record"]
    for key, (label, span) in marks.items():
        assert label in ("met", "unmet", "uncertain") and (not span or span in text), (key, label, span)
        if label == "met":
            assert span
            if "." in key:
                assert key.split(".")[0] in value["available"]
    if marks["citation"][0] == "met":
        citations = set(re.findall(r"\[(S\d+)\]", text))
        assert {"S0", "S1"} <= citations <= value["available"].keys()
    score = sum(points for key, points in fields.items() if marks[key][0] == "met")
    guarded = value["ended"] and len(text.split()) <= 145 and all(marks[key][0] == "met" for key in GUARDS)
    return {"points": score, "guarded_points": score if guarded else 0, "guarded": guarded,
            "strict": score == 70 and guarded, "ended": value["ended"], "words": len(text.split())}


def reordered(payoffs, permutation):
    return np.array([payoffs[sum(1 << destination for index, destination in enumerate(permutation)
                                 if mask & (1 << index))] for mask in range(8)])


def delivery_metrics(result, source_order):
    mass = result["receipt_distribution"]
    return {
        **result,
        "distinct_cards": sum(mask.bit_count() * p for mask, p in enumerate(mass)),
        "per_source_receipt_rate": {name: sum(p for mask, p in enumerate(mass) if mask & (1 << i))
                                    for i, name in enumerate(source_order)},
    }


def run_replay(final, writer):
    archive = json.loads(study.POLICY_ARCHIVE.read_text())
    agents = tuple(np.array(archive["training"][key]) for key in ("request", "left_delivery", "reply"))
    evaluated = {}
    sources = tuple(study.packet()["cards"])
    prior = route.TEST_PRIORS["uniform"]
    cases = {measure: [final[f"{writer}/{mask}"][measure] for mask in range(8)]
             for measure in ("points", "guarded_points", "strict")}
    for measure, rewards in cases.items():
        payoffs = np.asarray(rewards, dtype=float)
        matrix = route.receipt_matrix(payoffs, LOSS)
        independent = route.best_silent(prior, matrix)
        adaptive, maps = route.exact_optional(prior, matrix, LOSS)
        allowed = route.SEND[:, None, :, None] & route.SEND[None, :, None, :]
        pooled_net = float(np.sum(prior * np.where(allowed, matrix, -np.inf).max(axis=(2, 3))))
        adaptive_result = delivery_metrics(route.evaluate(adaptive, prior, payoffs, LOSS), sources)
        independent_result = delivery_metrics(route.evaluate(independent, prior, payoffs, LOSS), sources)
        assert independent_result["net"] <= adaptive_result["net"] + 1e-9 <= pooled_net + 2e-9
        order_results = {}
        for order in permutations(range(3)):
            position = "-".join(sources[j] for j in order)
            permuted = reordered(payoffs, order)
            arms = {name: delivery_metrics(route.evaluate(policy, prior, permuted, LOSS, force_missing=erased),
                                            tuple(sources[j] for j in order))
                    for name, policy, erased in (
                        ("frozen_fit", agents, False), ("same_policy_erased", agents, True),
                        ("fixed_priority_request", route.scripted(), False),
                    )}
            assert max(r["net"] for r in arms.values()) <= adaptive_result["net"] + 1e-8
            order_results[position] = arms
        summary = {}
        for label in arms:
            net = [row[label]["net"] for row in order_results.values()]
            summary[label] = {"min": min(net), "mean": sum(net) / len(net), "max": max(net)}
        evaluated[measure] = {
            "rewards_by_mask": rewards, "source_orders": order_results,
            "net_across_source_orders": summary,
            "exact_independent": independent_result, "exact_adaptive": adaptive_result,
            "pooled_two_send_ceiling": pooled_net,
            "requester_maps_enumerated": maps,
            "full_access_compiled_reward": rewards[7],
        }
    return {"loss": LOSS, "inventory": "uniform independent inventories over the eight masks",
            "new_optimizer_updates": 0, "results": evaluated}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    p.add_argument("--marks", type=Path)
    args = p.parse_args()
    records = views(args.directory)
    if args.marks:
        marks = json.loads(args.marks.read_text())
        assert marks.keys() == records.keys()
        final = {key: score_record(record, marks[key]) for key, record in records.items()}
        result = {"records": final, "frozen_policy_replay": {
            writer: run_replay(final, writer) for writer in ("bound", "normalized")
        }}
    else:
        result = records
    print(json.dumps(result, indent=2, ensure_ascii=False))
