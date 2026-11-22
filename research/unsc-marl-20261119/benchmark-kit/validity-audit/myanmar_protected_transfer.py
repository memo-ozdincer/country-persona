"""Score Myanmar record components and replay the frozen Mali policies by field assignment."""
import argparse
from hashlib import sha256
from itertools import permutations
import json
from pathlib import Path

import numpy as np

import mali_request_writer_review as judgment
import myanmar_protected_writer as writer
import source_request_policy as route

FROZEN = writer.TRAIN
DELIVERY_LOSS = .10
PUBLIC = ("vote", "mandate")
SOURCES = tuple(writer.FIELDS)
BRIDGE = (
    "The United Kingdom and India both emphasized regional consultation or concerns, while their votes "
    "differed [vote, uk, india]."
)


def annotation_rows(directory):
    raw = {r["id"]: r for r in writer.replay(directory)}
    annotations_path = directory / "annotations.json"
    labels = json.loads(annotations_path.read_text())
    assert labels["transcript_sha256"] == judgment.digest(directory / "transcript.jsonl")
    assert labels["components"].keys() == raw.keys()
    return raw, labels


def compose(directory):
    raw, labels = annotation_rows(directory)
    task = writer.packet()
    evidence = {b["id"]: b for b in task["evidence"]}
    sources = {k: evidence[k]["text"] for k in SOURCES}
    pieces = {}
    for field, row in raw.items():
        annotation = labels["components"][field]
        text = row["output"]
        assert text == annotation["candidate"] and annotation["reason"].strip()
        assert annotation["quote"] and annotation["quote"] in sources[field]
        if annotation["admit"]:
            assert row["ended"] and 0 < len(text.split()) <= writer.MAX_WORDS
            assert "[" not in text and "]" not in text
            pieces[field] = f"{text} [{field}]"
    capable = {key for key, row in labels["components"].items() if row.get("supports_overlap")}
    assert capable <= {"uk", "india"}
    paragraph = dict(zip(PUBLIC, writer.PUBLIC.split("\n\n"), strict=True))
    records = []
    for mask in route.STATES.tolist():
        available = [s for i, s in enumerate(SOURCES) if mask & (1 << i)]
        used = [s for s in available if s in pieces]
        bridge = BRIDGE if {"uk", "india"} <= set(used) & capable else ""
        answer = "\n\n".join(filter(None, [writer.PUBLIC, *(pieces[s] for s in used), bridge]))
        selected = [evidence[s] for s in [*PUBLIC, *available]]
        units = {}
        for key, source in writer.PUBLIC_UNITS.items():
            units[key] = (paragraph[source], (source,))
        for key, (needed, ids) in writer.RECEIPT_UNITS.items():
            if mask & needed != needed:
                continue
            if key == "overlap":
                if bridge:
                    units[key] = (bridge, ids)
            elif ids[-1] in used and labels["components"][ids[-1]]["criterion_met"]:
                # The two national vote criteria take evidence from the common roll call and local account.
                end = answer.index(pieces[ids[-1]]) + len(pieces[ids[-1]])
                units[key] = (answer[:end] if len(ids) > 1 else pieces[ids[-1]], ids)
        entries = []
        for unit in task["rubric"]:
            key = unit["id"]
            span, ids = units.get(key, ("", ()))
            assert set(ids) <= judgment.citations(span)
            cites = [{"block": s, "quote": evidence[s]["text"] if s in PUBLIC else labels["components"][s]["quote"]}
                     for s in ids]
            entries.append({"id": key, "status": "met" if span else "unmet", "response": span, "source": cites,
                            "reason": "The cited record and exact sources meet the criterion." if span else
                                      "The assembled record lacks the required supported claim."})
        # The maximum local output length and fixed bridge bound the assembled record.
        assert len(answer.split()) <= writer.RECORD_WORDS + len(BRIDGE.split())
        assert judgment.citations(answer) <= {row["id"] for row in selected}
        blind_bytes = json.dumps(["myanmar-final-v1", answer, [b["id"] for b in selected]]).encode()
        blind_id = sha256(blind_bytes).hexdigest()[:20]
        packet = {**task, "id": blind_id, "evidence": selected, "answer": answer}
        verdict = {"id": blind_id, "units": entries, "guard": {"status": "clear", "source": [],
                   "response": "", "reason": "Only the checked public section and admitted source-local claims were used."}}
        scored = judgment.score(packet, verdict)
        records.append({"mask": mask, "received": available, "used": used, "packet": packet,
                        "verdict": verdict, "points": scored["final"]["lower"], "complete": scored["strict"]})
    return records


def remap_policy(policy, order):
    """Conjugate the frozen policy from training IDs into a semantic field order."""
    action = np.asarray((0, *(i + 1 for i in order)))
    masks = np.asarray([sum(route.BITS[action[i]] for i in range(1, 4) if s & route.BITS[i])
                        for s in route.STATES])
    ask, send, reply = policy
    mapped = [np.zeros_like(ask), np.zeros_like(send), np.zeros_like(reply)]
    mapped[0][masks] = action[ask]
    mapped[1][masks] = action[send]
    mapped[2][np.ix_(masks, action)] = action[reply]
    return mapped


def intact_witness(policy, records):
    ask, send, reply = policy
    points = [r["points"] for r in records]
    best = None
    for left in route.STATES:
        for right in route.STATES:
            q, a = ask[left], send[left]
            b, neutral = reply[right, q], reply[right, 0]
            after, before = int(route.BITS[a] | route.BITS[b]), int(route.BITS[a] | route.BITS[neutral])
            if points[after] <= points[before] or best and points[after] - points[before] <= best["gain"]:
                continue
            best = {"left_available": int(left), "right_available": int(right),
                    "field_asked": SOURCES[q - 1],
                    "request_received_mask": after, "request_erased_mask": before,
                    "gain": points[after] - points[before]}
    return best


def run(directory, exact):
    bank = compose(directory)
    payoff = np.array([row["points"] for row in bank])
    full = np.array([row["complete"] for row in bank])
    trained = list(map(np.asarray, json.loads(FROZEN.read_text())["policy"]))
    script = route.scripted()
    matrix = route.receipt_matrix(payoff, DELIVERY_LOSS)
    cases = {}
    for name, prior in route.TEST_PRIORS.items():
        def assess(policy, erase=False):
            result = route.evaluate(policy, prior, payoff, DELIVERY_LOSS, force_missing=erase)
            result["complete_record_rate"] = float(np.array(result["receipt_distribution"]) @ full)
            return result
        best_silent = assess(route.best_silent(prior, matrix))
        # A centralized controller sees both private inventories before assigning
        # the same two delivery slots. Independent delivery cannot do this.
        feasible = np.logical_and(route.SEND[:, None, :, None], route.SEND[None, :, None, :])
        centralized = float(prior.ravel() @ np.where(feasible, matrix, -np.inf).max(axis=(2, 3)).ravel())
        arms = []
        for perm in permutations(range(3)):
            learned = remap_policy(trained, perm)
            arms.append({"field_order": [SOURCES[i] for i in perm], "learned": assess(learned),
                         "request_erased": assess(learned, erase=True),
                         "priority_script": assess(remap_policy(script, perm)),
                         "intact_link_witness": intact_witness(learned, bank)})
        case = {"exact_independent": best_silent, "assignments": arms,
                "centralized_inventory_oracle_net": centralized}
        if exact:
            upper, count = route.exact_optional(prior, matrix, DELIVERY_LOSS)
            case["exact_optional"] = {**assess(upper), "enumerated_requester_maps": count}
            assert case["exact_optional"]["net"] + 1e-9 >= max(
                [best_silent["net"], *(r[key]["net"] for r in arms for key in ("learned", "priority_script"))])
            assert centralized + 1e-9 >= case["exact_optional"]["net"]
        cases[name] = case
    return {"scope": "Frozen routing policy from Mali. Exposed Myanmar source family, excluded from this fit. "
            "Typed deliveries, independent model generations and same-assistant source adjudication.",
            "loss": DELIVERY_LOSS, "field_order": SOURCES, "policy_sha256": judgment.digest(FROZEN),
            "annotations_sha256": judgment.digest(directory / "annotations.json"),
            "records": bank, "two_delivery_points_ceiling": int(max(payoff[:-1])),
            "full_information_assembly_points": int(payoff[-1]), "priors": cases}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--directory", type=Path, default=writer.EVIDENCE / writer.FAMILY)
    cli.add_argument("--exact", action="store_true")
    cli.add_argument("--judge-packets", action="store_true")
    args = cli.parse_args()
    if args.judge_packets:
        packets = {r["packet"]["id"]: r["packet"] for r in compose(args.directory)}
        print("\n".join(json.dumps(p, ensure_ascii=False) for _, p in sorted(packets.items())))
    else:
        print(json.dumps(run(args.directory, args.exact), indent=2, ensure_ascii=False))
