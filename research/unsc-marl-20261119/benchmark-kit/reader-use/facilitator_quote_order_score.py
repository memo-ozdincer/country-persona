"""Replay both evidence-output orders through identical source-bound briefs."""
import argparse
from collections import Counter
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_quote_order as study
import facilitator_split_relation_score as prior
import facilitator_typed_clarification_score as compiled

HERE = study.HERE
MODES = (*study.ARMS, "archived_quote")
BASELINE = HERE / "facilitator-split-relation-evidence/results.json"
TRANSFER_TRACE = HERE / "facilitator-event-transfer-evidence/transcript.jsonl"


def targets():
    result = {}
    for panel, _, _, expected, _, _, _, _, _ in study.prior.typed.prior.source_inputs():
        result[panel] = compiled.rubric.RELATIONS[expected]
    for panel, _, _, truth, _ in study.held.panels():
        result[panel] = truth
    return result


def classify(rows):
    local_truth = targets()
    grades = {}
    for key, request in rows.items():
        panel, sid, mode, arm = key.split("/")
        prompt = json.loads(request["messages"][1]["content"])
        proposed, admitted, span = study.parse(request["output"], prompt["source"], arm)
        expected = local_truth[panel][int(sid[-1]) - 1]
        if not request["ended"]:
            admitted = "unknown"
        grades[key] = {"expected": expected, "proposed": proposed, "admitted": admitted, "witness": span,
                       "byte_exact": bool(span and span in prompt["source"]),
                       "copied_entire_source": span == prompt["source"],
                       "format_witness_ok": request["ended"] and (admitted != "unknown" or proposed == "unknown"),
                       "output": request["output"], "input_tokens": len(request["input_ids"]),
                       "output_tokens": len(request["output_ids"])}
    return grades


def fixed_transfer(receipts):
    old = study.base.load(prior.TRANSFER)
    old_quotes = study.base.load(prior.TRANSFER_READS)["readings"]
    packets = prior.archived_packets(old)
    base = compiled.replay.base
    all_cases, records = [], {}
    for packet, _, truth, seen, _, _ in study.held.packets():
        panel = packet.rsplit("/", 1)[0]
        expected = base.decision(truth, seen)
        item = packets[packet]
        assert expected == item["warranted"]
        options = {arm: tuple(receipts[f"{panel}/S{i}/direct/{arm}"]["admitted"] for i in (1, 2)) for arm in study.ARMS}
        options["archived_quote"] = tuple(old_quotes[f"{panel}/S{i}"]["quote"] for i in (1, 2))
        for arm, reads in options.items():
            action = base.decision(reads, seen)
            points = sum(item["body_criteria"].values()) + 14 * (action == expected)
            records[f"{packet}/{arm}"] = {"record": f"{action} |{item['body']}", "expected": expected,
                                          "decision": action, "points": points, "strict": points == 70}
            all_cases.append((panel, arm, seen, reads, expected, action, points == 70))
    simulated = compiled.route(all_cases, MODES)
    for prior_name, comparison in simulated.items():
        exact = old["replay"]["transfer"]["assertion"][prior_name]["quote_learned"]["mean"]["net_actionable"]
        assert abs(exact - comparison["frozen"]["summary"]["archived_quote"]["brief_net"]) < 1e-9
    return {"records": records, "replay": simulated}


def summaries(receipts):
    results = {}
    for key, row in receipts.items():
        panel, _, mode, arm = key.split("/")
        group = "clarification" if panel.startswith(("bosnia-", "afghanistan-")) else "transfer"
        report = results.setdefault(group, {}).setdefault(mode, {}).setdefault(arm, Counter())
        expected = row["expected"]
        got = row["admitted"]
        report["cases"] += 1
        report["correct"] += got == expected
        report["wrong_actionable_relation"] += got != expected and got != "unknown"
        report["missed_contradiction"] += expected == "contradicts" and got != expected
        report["witness_or_format_failure"] += not row["format_witness_ok"]
        report["entire_source_copied"] += row["copied_entire_source"]
        for k in ("input_tokens", "output_tokens"):
            report[k] += row[k]
    return results


def repeated_control(rows):
    archived = {row["id"]: row for row in map(json.loads, TRANSFER_TRACE.read_text().splitlines())
                if row["id"].endswith("/witness")}
    matched = {}
    for key, old in archived.items():
        panel_and_slot = key.removesuffix("/witness")
        now = rows[f"{panel_and_slot}/direct/relation_first"]
        matched[panel_and_slot] = {"same_messages": old["messages"] == now["messages"],
                                   "same_input_ids": old["input_ids"] == now["input_ids"],
                                   "same_output": old["output"] == now["output"],
                                   "archived_output": old["output"], "repeated_output": now["output"]}
    return matched


def run(directory):
    rows = study.read(directory)
    local = classify(rows)
    clarification = {}
    for arm in study.ARMS:
        relevant = {key.rsplit("/", 1)[0]: row for key, row in local.items()
                    if key.startswith(("bosnia-", "afghanistan-")) and key.endswith(f"/{arm}")}
        trace = {f"{key}/{arm}": rows[f"{key}/{arm}"] for key in relevant}
        with patch.object(compiled.study, "read", return_value=(trace, relevant)):
            # The renderer only needs the source relations. Hash this run's
            # generation capture in place of the older next-token trace.
            result = compiled.run(directory, capture="transcript.jsonl")
        clarification[arm] = result
    return {"scope": "Paired evidence-order prompt formats with literal witness admission. Gold labels are used "
                     "only to grade the relation and render the separately marked authored ceiling. Dockets were "
                     "previously exposed. Prior source-bound prose and routing policies remain fixed.",
            "generations": len(rows), "local_summary": summaries(local), "all_reads": local,
            "clarification": clarification, "transfer": fixed_transfer(local),
            "repeated_relation_first": repeated_control(rows),
            "input_sha256": {str(p.relative_to(HERE)): study.runner.digest(p)
                             for p in (BASELINE, prior.TRANSFER, prior.TRANSFER_READS, TRANSFER_TRACE)}}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    print(json.dumps(run(p.parse_args().directory), indent=2, ensure_ascii=False))
