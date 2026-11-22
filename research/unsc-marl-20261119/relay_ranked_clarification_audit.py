"""Replay a narrow reply into the learned ranked relay and audit its evidence."""
from collections import Counter
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import sys

import torch

import relay_compromise_joint as joint
import relay_ranked_clarification as clarify
from relay_ranked_mandates_audit import answered, readout, FIT


def replies(directory, questions, tasks):
    with clarify.inputs():
        raw = clarify.mandate.language.scorer.read(directory)
    results = {}
    for (family, role, identity, rotation, _), row in sorted(raw.items()):
        request = questions[family, role, identity]
        values = [card[request["package_index"]] for card in tasks[family].cards[role]]
        reply = clarify.ORDERS[rotation][max(range(4), key=row["scores"].__getitem__)]
        matching = [i for i, value in enumerate(values) if value == reply]
        results[family, role, identity, rotation] = {
            "grade": reply, "grade_is_true": values[identity] == reply,
            "scores": row["scores"], "compatible_profiles": matching,
            "revision": matching[0] if len(matching) == 1 else None,
        }
    return results


def revised_card(primary, reply):
    if reply is None:
        return primary
    compatible = reply["compatible_profiles"]
    if reply["revision"] is not None:
        return reply["revision"]
    return primary if primary in compatible else None


def rollout(task, policy, table, true_ids, claims, requests, reply_scores):
    world = (task.first[true_ids[0]], task.second[true_ids[1]])
    domains = (task.first, task.second)
    expected = answered(task, *world)
    case_routes = {}
    for lab, seat in (("no_query", None), ("relay_only", 0), ("far_only", 1),
                      ("lowest_margin", min(range(2), key=lambda r: requests[r]["margin"]))):
        for mode in (("first_order", "rotated", "consensus") if seat is not None else ("none",)):
            cards = list(claims)
            receipt = None
            if seat is not None:
                candidates = [reply_scores[task.name, seat, true_ids[seat], k] for k in range(2)]
                receipt = (candidates[0] if mode in ("first_order", "consensus") else candidates[1])
                if mode == "consensus" and candidates[0]["grade"] != candidates[1]["grade"]:
                    receipt = None
                cards[seat] = revised_card(claims[seat], receipt)
            sent = tuple(domain[code] if code is not None else 0 for domain, code in zip(domains, cards, strict=True))
            trace = joint.routed(task, policy, sent, "peer")
            delivered = joint.ranked.delivered(trace)
            verified = tuple(v if v == t else 0 for v, t in zip(delivered, world, strict=True))
            warrant = answered(task, *verified)
            choice = readout(table, policy, task, *delivered)
            case_routes[lab, mode] = {
                "query_seat": seat, "question": requests[seat] if seat is not None else None,
                "reply": receipt, "claims": claims, "revised_claims": cards, "received": delivered,
                "false_cards": sum(bool(value) and value != actual for value, actual in zip(delivered, world, strict=True)),
                "warrant": sorted(warrant), "choice": choice,
                "valid": choice in expected, "warranted": choice in warrant,
                "completed": choice in warrant and choice != "unresolved",
                "trace": trace["deliveries"],
            }
    return {"world": world, "optima": sorted(expected),
            "arms": {f"{lab}/{mode}": r for (lab, mode), r in case_routes.items()}}


def audit(directory):
    torch.set_num_threads(1)
    tasks = clarify.mandate.language.ranked.fixtures()
    questions = {tuple(q["key"]): q for q in clarify.questions()}
    answers = replies(directory, questions, tasks)
    policy = joint.Joint(True)
    weights = json.loads(FIT.read_text())["training"]["qwen_joint"]["state"]
    policy.load_state_dict({name: torch.tensor(v) for name, v in weights.items()})
    table = joint.unpack()
    results = {}
    with torch.no_grad():
        for family, task in tasks.items():
            rows = []
            for world in product(range(3), repeat=2):
                demands = [questions[family, seat, choice] for seat, choice in enumerate(world)]
                claims = tuple(q["claimed"] for q in demands)
                rows.append(rollout(task, policy, table, world, claims, demands, answers))
            results[family] = rows
    separate = [{"key": k, **v, "public_query": questions[k[:3]]} for k, v in answers.items()]
    report = {"source_sha256": sha256((directory/"actions.jsonl").read_bytes()).hexdigest(),
              "outcomes": results, "reply_observations": separate}
    report["counts"] = {f"{family}/{arm}": value for (family, arm), value in summary(report).items()}
    return report


def summary(report):
    counts = {}
    for family, rows in report["outcomes"].items():
        for world in rows:
            for label, record in world["arms"].items():
                key = (family, label)
                counter = counts.setdefault(key, Counter())
                for field in ("false_cards", "valid", "warranted", "completed"):
                    counter[field] += record[field]
                counter["unsupported_decision"] += record["choice"] != "unresolved" and not record["warranted"]
    return counts


if __name__ == "__main__":
    report = audit(Path(sys.argv[1]))
    print(json.dumps(report, indent=2))
