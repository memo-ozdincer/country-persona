"""Check live request and payload fidelity, then reassemble the exact reviewed outcome."""
import argparse
import json
from pathlib import Path

import facilitator_live_delivery as live


def counts(row):
    return {"input": len(row["input_ids"]), "output": len(row["output_ids"])}


def run(rows):
    report = {}
    for key, name, episode in live.episodes():
        bank, notes = live.bank(name)
        arrived = episode["opening_receipts"]
        openings_cost = .2 * sum(x != 0 for x in episode["opening_attempts"])
        arms = {}
        for arm, intent in episode["arms"].items():
            q = intent["query"]
            conversational_view = rows[f"{key}/query/{q}"]
            recovered = live.heard(rows, key, q)
            card = intent["reply"][recovered]
            deliver = rows[f"{key}/payload/{card}"]
            correct = deliver["ended"] and deliver["output"] == (notes[card] or "NONE")
            mask = int(arrived | live.ROUTE.BITS[card if correct else 0])
            record = bank[mask]
            if correct and card:
                assert deliver["output"] in record["text"]
            typed = bank[intent["typed_final"]]
            fee = openings_cost + .05 * (q != 0) + .2 * (card != 0)
            arms[arm] = {
                "typed_expectation": {"request": q, "send": intent["typed_sent"], **typed},
                "question": (live.TOPICS[name][q - 1][1] if q else ""),
                "decode": conversational_view["output"], "heard_topic": recovered, "correct_request": recovered == q,
                "payload": deliver["output"], "requested_send": card, "payload_pass": correct,
                "received_card": card if correct else 0, "record": record, "fees": fee,
                "net": record["points"] + 21 * record["strict"] - fee,
                "calls": {k: counts(v) for k, v in (("decode", conversational_view), ("payload", deliver))},
            }
        report[key] = {**episode, "arms": arms}
    totals = {
        arm: {
            "typed_masks_preserved": sum(row["arms"][arm]["record"]["mask"] == row["arms"][arm]["typed_expectation"]["mask"]
                                         for row in report.values()),
            "strict_records": sum(row["arms"][arm]["record"]["strict"] for row in report.values()),
            "guarded_points": sum(row["arms"][arm]["record"]["points"] for row in report.values()),
        } for arm in live.ARMS
    }
    return {"scope": "Four deliberately chosen branch diagnostics with actual language decoder and payload calls. "
                     "Pre-admitted note text and the full mask-specific assembly are held fixed.",
            "physical_calls": len(rows), "logical_calls": len(report) * len(live.ARMS) * 2,
            "all_decodes_match": all(x["correct_request"] for r in report.values() for x in r["arms"].values()),
            "all_payloads_match": all(x["payload_pass"] for r in report.values() for x in r["arms"].values()),
            "totals": totals, "episodes": report}


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    print(json.dumps(run(live.verify(cli.parse_args().directory)), indent=2, ensure_ascii=False))
