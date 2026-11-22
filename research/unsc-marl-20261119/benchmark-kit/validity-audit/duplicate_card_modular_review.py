"""Score assembled model text against the same Venezuela route benchmark."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

from duplicate_card_modular import CASE, compose
from duplicate_card_records import CARD_IDS, FIT
from duplicate_card_score import ASSIGNED, summarize_routes
import source_record_review as review


def bundle(directory):
    case = json.loads(CASE.read_text())
    records = compose(directory)["records"]
    deck, join = {}, {}
    for row in records:
        ident = f"{case['family']}/{row['receipt']}/chair"
        key = sha256(("venezuela-routing/" + ident).encode()).hexdigest()[:10]
        deck[key] = {"criteria": case["criteria"], "critical_errors": case["critical_errors"],
                     "evidence": row["evidence"], "candidate": row["record"]}
        join[key] = ident
    return dict(sorted(deck.items())), join


def score(directory):
    annotation_path = directory / "annotations.json"
    annotations = json.loads(annotation_path.read_text())
    deck, join = bundle(directory)
    with patch.object(review, "bundle", new=bundle):
        ratings = review.score(directory, annotations)
    raw = compose(directory)
    rows = {row["receipt"]: row for row in raw["records"]}
    packets = {}
    public_grades = None
    for key, ident in join.items():
        receipt = ident.split("/")[-2]
        row = rows[receipt]
        units = annotations["reviews"][key]["units"]
        met = [unit for unit, mark in units.items() if mark[0] == "met"]
        visible = frozenset(source for source in ASSIGNED.values() if source in deck[key]["evidence"])
        assert all(ASSIGNED[unit] in visible for unit in ASSIGNED if unit in met)
        scores = {unit: mark[0] for unit, mark in units.items() if unit not in ASSIGNED}
        if public_grades is None:
            public_grades = scores
        assert public_grades == scores
        packets[visible] = {"id": ident, **ratings[ident], "met_units": met, "ended": row["ended"],
                            "input_tokens": row["input_tokens"], "completion_tokens": row["output_tokens"],
                            "completion_cap": row["output_token_cap"], "model_calls": len(row["component_ids"])}
    for unit, source in ASSIGNED.items():
        counts = {unit in packet["met_units"] for visible, packet in packets.items() if source in visible}
        assert len(counts) == 1  # Identical independently assessed text wherever a card is present.
    return {"scope": annotations["scope"], "annotation_sha256": sha256(annotation_path.read_bytes()).hexdigest(),
            "transcript_sha256": raw["source_transcript_sha256"], "packet_scores": list(packets.values()),
            "arms": summarize_routes(packets)}


def cost_audit(directory):
    fields = ("model_calls", "input_tokens", "output_tokens", "output_token_cap")
    modular = {r["receipt"]: {**r, "model_calls": len(r["component_ids"])} for r in compose(directory)["records"]}
    writers = {"modular": modular}
    for arm in ("writer", "slots"):
        baseline = directory.with_name(arm) / "transcript.jsonl"
        writers[arm] = {row["id"].split("/")[-2]: {"model_calls": 1, "input_tokens": len(row["input_ids"]),
                         "output_tokens": len(row["output_ids"]), "output_token_cap": row["cap"]}
                        for row in map(json.loads, baseline.read_text().splitlines())}
    costs = {}
    for prior, arms in json.loads(FIT.read_text())["arms"].items():
        costs[prior] = {}
        for route, entry in arms.items():
            receipts = []
            for row in entry["worlds"]:
                delivered = {CARD_IDS[action] for action in row["actions"] if action}
                receipt = "-".join(card for card in CARD_IDS if card in delivered) or "public"
                receipts.append((row["probability"], receipt))
            costs[prior][route] = {
                writer: {field: sum(probability * packets[receipt][field] for probability, receipt in receipts)
                         for field in fields}
                for writer, packets in writers.items()
            }
    return costs


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    modes = cli.add_mutually_exclusive_group()
    modes.add_argument("--score", action="store_true")
    modes.add_argument("--costs", action="store_true")
    args = cli.parse_args()
    if args.costs:
        result = cost_audit(args.directory)
    else:
        result = score(args.directory) if args.score else bundle(args.directory)[0]
    print(json.dumps(result, ensure_ascii=False, indent=2))
