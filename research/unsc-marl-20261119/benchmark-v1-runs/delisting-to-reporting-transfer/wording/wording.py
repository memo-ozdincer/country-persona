"""Collect fresh source margins and evaluate the frozen transfer under paraphrases."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from statistics import mean
import sys
from unittest.mock import patch

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import transfer

source = transfer.TARGET
read = transfer.fit.read
from collect_transfer_dockets import cpu, collector

PARAPHRASES = {
    "full": (
        "Algeria abstained as it had in January. Its representative said the Secretary-General's monthly accounts "
        "of attacks on commercial shipping helped keep Council members informed. Algeria gave a separate reason "
        "for abstaining: concerns about the way resolution 2722 (2024) was implemented, including what it "
        "considered misuse or misreading of self-defence in attacks on sovereign territory."
    ),
    "objection": (
        "Algeria explained its abstention by pointing to implementation of resolution 2722 (2024). "
        "It believed self-defence had been misused or misinterpreted in attacks on sovereign territory."
    ),
    "voted-only": "Algeria abstained on the draft.",
}


def plan():
    original = read(source/"plan.json")
    requests = []
    for request in original["requests"]:
        if not request["id"].startswith("2739/early/"):
            continue
        key, label = request["id"].split("/")[2:]
        changed = deepcopy(request)
        changed["id"] = f"updated/{key}/{label}"
        payload = json.loads(changed["messages"][1]["content"])
        payload["source_text"] = PARAPHRASES[key]
        changed["messages"][1]["content"] = json.dumps(payload, ensure_ascii=False)
        requests.extend((request, changed))
    paths = (Path(__file__), HERE/"protocol.md", HERE.parent/"plan.json",
             HERE.parent/"results.json", source/"plan.json", source/"verified.json")
    return {"requests": requests, "checkpoint_index_sha256": original["checkpoint_index_sha256"],
            "pins": {str(path.relative_to(transfer.RUNS)): transfer.digest(path) for path in paths}}


def evaluate(spec):
    captured = read(HERE/"verified.json")["outputs"]
    archived = read(source/"verified.json")["outputs"]
    cases = read(source/"plan.json")["cases"]
    target = read(HERE.parent/"plan.json")
    team = transfer.team
    sender = np.zeros((2, 3, 5))
    receiver = np.zeros((2, 3))
    for i, view in enumerate(target["target_views"]):
        donor = target["source_views"].index(target["sender_binding"][view])
        sender[1, i] = target["sender_weights"][donor]
        if not target["send_eligible"][i]:
            sender[1, i, 0] = -1e6
    fallback = read(HERE.parent/"results.json")["receiver_actions"]["semantic_default"]
    receiver[1] = np.array(fallback)*2 - 1

    results = {}
    variants = {"fresh_original": set(), "paraphrases": {"full", "objection"},
                "complete_attribution": {"full", "objection", "voted-only"}}
    for name, changed in variants.items():
        outputs = dict(archived)
        for key in PARAPHRASES:
            for order in ("ab", "ba"):
                ident = f"2739/early/{key}/{order}"
                fresh = f"updated/{key}/{order}" if key in changed else ident
                outputs[ident] = captured[fresh]
        _, bank, _, records = transfer.fit.bank(cases, outputs)
        real_records = {key: row for key,row in records.items() if key.startswith("2739/")}
        report = {}
        with patch.object(team, "PRIVATE", {key: tuple(case["early"]) for key,case in cases.items()}):
            for group, prices in target["grid"].items():
                with patch.object(team, "TEST_PRICES", tuple(prices)):
                    comparison = transfer.fit.learner.fit.compare(bank, (sender,receiver), (sender,receiver))
                chosen = [row for row in comparison["held"] if row["family"] == "2739"]
                report[group] = comparison["mean_utility"]["2739"] | {
                    "mean_send_cost": round(mean(row["native_fit"]["cost"] for row in chosen), 8),
                    "wins": sum(row["native_fit"]["utility"] > row["best_arrival_only"]["utility"] for row in chosen),
                }
        results[name] = {
            "margins": {key: transfer.fit.margin(outputs, f"2739/early/{key}") for key in PARAPHRASES},
            "released_pairs": {key: row["audited_score"] for key,row in real_records.items()},
            "results": report,
        }
    return {"variants": results, "fresh_original_logits_match": {
        row["id"]: captured[row["id"]]["logits"] == archived[row["id"]]["logits"]
        for row in spec["requests"] if row["id"].startswith("2739/")
    }}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "verify", "score"))
    mode = parser.parse_args().mode
    spec = plan()
    if mode != "plan":
        assert spec == read(HERE/"plan.json")
    if mode in {"run", "verify"}:
        with patch.object(cpu, "HERE", HERE), patch.object(cpu, "OUT", HERE/"evidence"), patch.object(
            cpu, "locked", return_value=spec
        ):
            result = {"run": cpu.run, "verify": cpu.verify}[mode]()
    elif mode == "score":
        result = evaluate(spec)
    else:
        result = spec
    if mode != "run":
        print(json.dumps(result, ensure_ascii=False, indent=2))
