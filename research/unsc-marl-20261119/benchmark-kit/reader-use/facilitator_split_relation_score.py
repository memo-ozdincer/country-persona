"""Score split source judgments with the existing speakers, records and delivery policies."""
import argparse
from collections import Counter
import json
from pathlib import Path
from unittest.mock import patch

import facilitator_split_relation as study
import facilitator_typed_clarification_score as compiled

HERE = study.HERE
TRANSFER = HERE / "facilitator-witness-writer-evidence/results.json"
TRANSFER_READS = HERE / "facilitator-event-transfer-evidence/results.json"
TYPED = HERE / "facilitator-typed-clarification-evidence/results.json"
TYPED_TRACE = TYPED.with_name("actions.jsonl")
TRANSFER_MODES = ("binary", "three_way", "quote")


def local_counts(predictions):
    summaries = {}
    for mode, cases in predictions.items():
        totals = Counter()
        for expected, got in cases:
            totals["count"] += 1
            totals["correct"] += expected == got
            totals["wrong_actionable"] += got != expected and got != "unknown"
            totals["missed_contradiction"] += expected == "contradicts" and got != expected
            totals["deferrals_on_determinate"] += expected != "unknown" and got == "unknown"
        summaries[mode] = totals
    return summaries


def order_audit(logits, reads):
    target = {}
    for panel, _, _, expected, _, _, _, _, _ in study.typed.prior.source_inputs():
        target[panel] = compiled.rubric.RELATIONS[expected]
    for panel, _, _, relations, _ in study.transfer.panels():
        target[panel] = relations
    checks = {}
    for order in (0, 1):
        for check in study.CHECKS:
            records = [row for key, row in logits.items() if key[-2:] == (check, order)]
            letters = Counter("tie" if (picked := study.protocol.delivery.choose(row)) is None
                              else "AB"[row["legal"].index(picked)] for row in records)
            checks[f"{check}/{order}"] = dict(letters)
    alternatives = {}
    for key, item in reads.items():
        panel, sid, mode = key.split("/")
        scope = "clarification" if panel.startswith(("bosnia-", "afghanistan-")) else "transfer"
        reference = target[panel][int(sid[-1]) - 1]
        for n in (0, 1):
            support = item["checks"]["support"]["votes"][n] == "yes"
            conflict = item["checks"]["incompatibility"]["votes"][n] == "yes"
            read = ("supports" if support else "contradicts") if support != conflict else "unknown"
            alternatives.setdefault(f"{scope}/{mode}/order{n}", []).append((reference, read))
    return {"selected_letters": checks, "single_order_local_diagnostic": local_counts(alternatives)}


def archived_packets(archive):
    packets = {}
    for key, item in archive["records"]["assertion"].items():
        if not key.startswith(("abyei-", "central-african-republic-")):
            continue
        prefix, _ = key.rsplit("/", 1)
        ref = item["grade"]
        body = item["record"].partition("|")[2]
        criteria = {k: n for k, n in ref["criteria"].items() if k != "disposition"}
        packet = {"warranted": ref["expected"], "body": body, "body_criteria": criteria}
        assert packets.setdefault(prefix, packet) == packet
    assert len(packets) == 16
    return packets


def transfer(reads):
    load = study.typed.prior.base.load
    base = compiled.replay.base
    old = load(TRANSFER)
    quote = load(TRANSFER_READS)["readings"]
    packets = archived_packets(old)
    predictions = {mode: [] for mode in TRANSFER_MODES}
    cases, finals = [], {}
    for packet, _, truth, seen, _, _ in study.transfer.packets():
        claim, _ = packet.rsplit("/", 1)
        reference = base.decision(truth, seen)
        old_packet = packets[packet]
        assert old_packet["warranted"] == reference
        vectors = {}
        for mode in TRANSFER_MODES:
            by_sid = [reads[f"{claim}/S{i}/direct"] for i in (1, 2)]
            if mode == "binary":
                vector = tuple(item["admitted"] for item in by_sid)
            elif mode == "three_way":
                vector = tuple(item["checks"]["three_way"]["admitted"] for item in by_sid)
            else:
                vector = tuple(quote[f"{claim}/S{i}"]["quote"] for i in (1, 2))
            vectors[mode] = vector
            action = base.decision(vector, seen)
            points = sum(old_packet["body_criteria"].values()) + 14 * (action == reference)
            finals[f"{packet}/{mode}"] = {"record": f"{action} |{old_packet['body']}",
                                          "reference": reference, "action": action, "points": points, "strict": points == 70}
            cases.append((claim, mode, seen, vector, reference, action, points == 70))
        if seen == base.TARGETS:
            for mode in TRANSFER_MODES:
                predictions[mode].extend(zip(truth, vectors[mode], strict=True))
    with patch.object(compiled.replay, "MODES", TRANSFER_MODES):
        # route sets its own mode tuple for the clarification panels.
        read_policy = load(compiled.FEEDBACK)["independent_policy"]
        independent = {compiled.freeze(row["state"]): row["probabilities"] for row in read_policy}
        frozen = study.transfer.chair.transfer.policy(study.transfer.chair.transfer.FROZEN)
        systems = (("frozen", "learned", frozen), ("frozen_erased", "learned_erased", frozen),
                   ("independent", "learned_erased", independent), ("greedy", "greedy", {}))
        result = {inventory: compiled.replay.evaluate(compiled.replay.collect(cases), systems, inventory)
                  for inventory in ("split", "overlap")}
    for inventory, compare in result.items():
        old_net = old["replay"]["transfer"]["assertion"][inventory]["quote_learned"]["mean"]["net_actionable"]
        assert abs(compare["frozen"]["summary"]["quote"]["brief_net"] - old_net) < 1e-9
    return {"local": local_counts(predictions), "records": finals, "delivery": result}


def score(directory):
    logits, reads = study.read(directory)
    main = {k: v for k, v in reads.items() if k.startswith(("bosnia-", "afghanistan-"))}
    with patch.object(compiled.study, "read", return_value=(logits, main)):
        new = compiled.run(directory)
    old = study.typed.prior.base.load(TYPED)
    token_tallies = Counter()
    calls = Counter()
    for key, row in logits.items():
        scope = "clarification" if key[0].startswith(("bosnia-", "afghanistan-")) else "transfer"
        mode = "binary" if key[-2] != "three_way" else "three_way"
        token_tallies[f"{scope}/{mode}"] += len(row["input_ids"])
        calls[f"{scope}/{mode}"] += 1
    prior_rows = [json.loads(line) for line in TYPED_TRACE.read_text().splitlines()]
    token_tallies["clarification/three_way"] = sum(len(row["input_ids"]) for row in prior_rows)
    calls["clarification/three_way"] = len(prior_rows)
    return {"scope": "Distinct support and incompatibility probes, each in both option orders. Authored source "
                     "cards and same-assistant prose reviews are unchanged. The transfer dossiers were used "
                     "previously and are separate from the immediate clarification failure cases. No refit.",
            "prompt_count": len(logits), "classification": reads, "clarification": new,
            "option_order_diagnostic": order_audit(logits, reads),
            "inference": {k: {"calls": calls[k], "input_tokens": n} for k, n in token_tallies.items()},
            "previous_three_way": {"local": old["local_accuracy"], "complete": old["summary"],
                                   "split": old["simulated_delivery"]["split"]},
            "transfer": transfer(reads),
            "input_sha256": {str(p.relative_to(HERE)): study.typed.prior.runner.digest(p)
                             for p in (TRANSFER, TRANSFER_READS, TYPED, TYPED_TRACE)}}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    print(json.dumps(score(p.parse_args().directory), indent=2, ensure_ascii=False))
