"""Compile and grade held Resolution 2739 receipts independently of inference."""
import argparse
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from statistics import mean
import sys

HERE = Path(__file__).resolve().parent
ADMISSION = HERE.parent
CASE_DIR = ADMISSION.parent
RELEASE = CASE_DIR.parents[1] / "benchmark-v1.5"
sys.path[:0] = [str(RELEASE), str(ADMISSION)]
import evaluate as e
import team

CASE = e.read(CASE_DIR / "docket.json")
OWNER = {"algeria": 1, "sponsors": 2}
COMMON = ("algeria-reporting", "sponsors-informed-deliberation")
SHARED = ("Both delegations saw continued Secretary-General reporting as a way to keep the Council "
          "informed. Algeria nevertheless abstained on the resolution.")
PUBLIC = ("The Council adopted Japanese–US draft S/2024/500 as resolution 2739 (2024), 12–0–3. "
          "Algeria, China and Russia abstained. It extended the Secretary-General’s reporting request "
          "under paragraph 10 of resolution 2722 (2024) through 15 January 2025, without granting "
          "new authority for military action.")
CORE = {
    "disposition": ("vote", "adopted Japanese–US draft S/2024/500 as resolution 2739 (2024), 12–0–3. Algeria, China and Russia abstained."),
    "draft-and-sponsors": ("vote", "Japanese–US draft S/2024/500"),
    "operative-report": ("action", "extended the Secretary-General’s reporting request under paragraph 10 of resolution 2722 (2024) through 15 January 2025"),
    "authority": ("action", "without granting new authority for military action"),
}
POLICIES = ("fitted_greedy", "consensus", "first_only", "pooled_mean", "privileged_semantic")
BLOCKS = e.judge.by_id(e.evidence(CASE))


def hash_bytes(path):
    return sha256(path.read_bytes()).hexdigest()


def data_files():
    return (Path(__file__), HERE / "protocol.md", ADMISSION / "held.json", ADMISSION / "fit.json",
            ADMISSION / "verified.json", ADMISSION / "results.json", ADMISSION / "evidence/calls.jsonl",
            CASE_DIR / "docket.json", RELEASE / "release.json")


def plan():
    return {"policies": list(POLICIES), "receipt_masks": list(range(4)), "orders": [0, 1],
            "inputs": {str(path.relative_to(team.STUDY)): hash_bytes(path) for path in data_files()}}


def admissions(candidates, fitted, order):
    result = dict.fromkeys(POLICIES[:-1], "unknown")
    first, second = candidates[order], candidates[1 - order]
    first_features, second_features = team.features(first, second)
    local, peer = first[1], second[1]
    if local != 2:
        result["first_only"] = team.LABELS[local]
        if local == peer:
            result["consensus"] = team.LABELS[local]
        send = first_features @ fitted["proposer"]
        approve = second_features @ fitted["reviewer"]
        if send >= 0 and approve >= 0:
            result["fitted_greedy"] = team.LABELS[local]
    mean_scores = (first[0] + second[0]) / 2
    _, label = team.mapped({"legal": [0, 1, 2], "scores": mean_scores})
    result["pooled_mean"] = team.LABELS[label]
    return result


def publish(admitted, registry, mask):
    statements = {}
    for key in admitted:
        receipt = registry[key]
        block = receipt["source"]
        if block in OWNER and mask & OWNER[block]:
            assert BLOCKS[block]["text"].count(receipt["witness"]) == 1
            statements[key] = receipt["assertion"]
    parts = [PUBLIC, *statements.values()]
    if set(COMMON) <= statements.keys():
        parts.append(SHARED)
    return " ".join(parts), statements


def judge(text, statements, registry, gold):
    packet = e.final_packet(CASE, [{}, {}, {"text": text}])
    credited = {key: ([block], span) for key, (block, span) in CORE.items()}
    if COMMON[1] in statements:
        credited["sponsor-reason"] = (["sponsors"], statements[COMMON[1]])
    if set(COMMON) <= statements.keys():
        credited["bounded-overlap"] = (["sponsors", "algeria"], SHARED)
    unsupported = [k for k in statements if gold[k] != "supports"]

    def witness(ids):
        return [{"block": registry[key]["source"], "quote": registry[key]["witness"]} for key in ids]

    def cite(unit, blocks):
        if unit == "bounded-overlap":
            return witness(COMMON)
        if unit == "sponsor-reason":
            return witness([COMMON[1]])
        return [{"block": block, "quote": BLOCKS[block]["text"]} for block in blocks]

    guard = ({"status": "failed", "source": witness([unsupported[0]]), "response": statements[unsupported[0]],
              "reason": "Published candidate exceeds its source witness."} if unsupported else
             {"status": "clear", "source": [], "response": "", "reason": "Each published claim is supported."})
    units = []
    for spec in CASE["rubric"]:
        key = spec["id"]
        blocks, span = credited.get(key, ([], ""))
        units.append({"id": key, "source": cite(key, blocks) if span else [], "response": span,
                      "status": "met" if span else "unmet",
                      "reason": spec["rule"] if span else "An evidentiary element is absent."})
    verdict = {"id": packet["id"], "units": units, "guard": guard}
    calls = [{}, {}, {"text": text, "termination": "complete"}]
    return {"score": e.final_score(CASE, calls, verdict), "verdict": verdict,
            "unsupported_assertions": unsupported}


def benchmark():
    assert plan() == e.read(HERE / "plan.json")
    held = e.read(ADMISSION / "held.json")
    registry = {row["id"]: {k: v for k, v in row.items() if k != "expected"} for row in held}
    gold = {row["id"]: row["expected"] for row in held}
    assert len(held) == len(registry) == len(gold) == 8
    observed = team.observations(ADMISSION / "evidence/calls.jsonl", "held")
    weights = e.read(ADMISSION / "fit.json")["frozen"]
    prior = e.judge.by_id([r | {"id": r["key"]} for r in e.read(ADMISSION / "results.json")["held_rows"]])
    assert set(observed) == set(registry)
    records, messages = {}, {}
    for order in (0, 1):
        labels = {key: admissions(value, weights, order) for key, value in observed.items()}
        messages[str(order)] = labels
        for key, values in labels.items():
            for policy, choice in values.items():
                old = prior[key]["orders"][str(order)]["policies"][policy]
                assert int(choice != "unknown" and choice == gold[key]) == old["true_admission"]
                assert int(choice != "unknown" and choice != gold[key]) == old["wrong_admission"]
        for policy, mask in product(POLICIES, range(4)):
            admit = [key for key in registry if (gold[key] if policy == "privileged_semantic"
                                                else labels[key][policy]) == "supports"]
            text, statements = publish(admit, registry, mask)
            review = judge(text, statements, registry, gold)
            records[f"{order}/{policy}/{mask}"] = review | {"received": list(statements), "record": text}
            assert review["score"]["words"] <= CASE["word_cap"]
    assert len(records) == 40
    for order, mask in product((0, 1), range(4)):
        assert records[f"{order}/fitted_greedy/{mask}"] == records[f"{order}/consensus/{mask}"]
    return {"decisions_before_delivery": messages, "records": records,
            "means": {arm: {"full_receipt_released": mean(records[f"{order}/{arm}/3"]["score"]["released_70"]
                                                          for order in (0, 1)),
                            "uniform_receipt_released": mean(records[f"{order}/{arm}/{mask}"]["score"]["released_70"]
                                                             for order, mask in product((0, 1), range(4))),
                            "guard_failures": sum(bool(records[f"{order}/{arm}/{mask}"]["unsupported_assertions"])
                                                  for order, mask in product((0, 1), range(4)))}
                      for arm in POLICIES}, "plan_sha256": hash_bytes(HERE / "plan.json")}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run"))
    e.emit({"plan": plan, "run": benchmark}[parser.parse_args().mode]())
