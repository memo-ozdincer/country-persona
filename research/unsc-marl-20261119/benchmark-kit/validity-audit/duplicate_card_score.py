"""Apply exact-span review and replay each Venezuela evidence route."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from unittest.mock import patch

from duplicate_card_records import CARD_IDS, CASE, FIT
from duplicate_card_writer import suite
import source_record_review as reviewer

ASSIGNED = {"P1": "CHAIR", "P2": "INDONESIA"}


def bundle(directory):
    case = json.loads(CASE.read_text())
    candidates = list(map(json.loads, (directory / "transcript.jsonl").read_text().splitlines()))
    deck, join = {}, {}
    for row, expected in zip(candidates, suite(), strict=True):
        assert all(row[key] == value for key, value in expected.items())
        evidence = json.loads(row["messages"][-1]["content"])["evidence"]
        key = sha256(("venezuela-routing/" + row["id"]).encode()).hexdigest()[:10]
        deck[key] = {"criteria": case["criteria"], "critical_errors": case["critical_errors"],
                     "evidence": evidence, "candidate": row["output"]}
        join[key] = row["id"]
    return dict(sorted(deck.items())), join


def score(directory):
    path = directory / "annotations.json"
    annotations = json.loads(path.read_text())
    deck, join = bundle(directory)
    with patch.object(reviewer, "bundle", new=bundle):
        ratings = reviewer.score(directory, annotations)
    packets = {}
    raw = {row["id"]: row for row in map(json.loads, (directory / "transcript.jsonl").read_text().splitlines())}
    for key, ident in join.items():
        grades = annotations["reviews"][key]["units"]
        met = [unit for unit, result in grades.items() if result[0] == "met"]
        visible = deck[key]["evidence"]
        assert all(ASSIGNED[unit] in visible for unit in ASSIGNED if unit in met)
        ids = frozenset(card for card in ASSIGNED.values() if card in visible)
        packets[ids] = {"id": ident, **ratings[ident], "met_units": met,
                        "completion_tokens": len(raw[ident]["output_ids"]), "ended": raw[ident]["ended"]}
    return {"scope": annotations["scope"], "annotation_sha256": sha256(path.read_bytes()).hexdigest(),
            "transcript_sha256": sha256((directory / "transcript.jsonl").read_bytes()).hexdigest(),
            "packet_scores": list(packets.values()), "arms": summarize_routes(packets)}


def summarize_routes(packets):
    summaries = {}
    for prior, arms in json.loads(FIT.read_text())["arms"].items():
        summaries[prior] = {}
        for arm, results in arms.items():
            weighted = [(row["probability"], packets[frozenset(CARD_IDS[a] for a in row["actions"] if a)])
                        for row in results["worlds"]]
            def probability(predicate):
                return sum(p for p, packet in weighted if predicate(packet))
            summaries[prior][arm] = {
                "mean_verified_record": sum(p * packet["floor"] for p, packet in weighted),
                "mean_optimistic_record": sum(p * packet["ceiling"] for p, packet in weighted),
                "national_position_probability": {
                    key: probability(lambda packet: key in packet["met_units"]) for key in ASSIGNED
                },
                "both_positions_probability": probability(lambda packet: set(ASSIGNED) <= set(packet["met_units"])),
                "confirmed_critical_error_probability": probability(lambda packet: packet["critical_guard"] == "failed"),
                "uncertain_guard_probability": probability(lambda packet: packet["critical_guard"] == "uncertain"),
                "over_160_words_probability": probability(lambda packet: not packet["under_limit"]),
                "over_requested_120_words_probability": probability(lambda packet: packet["words"] > 120),
                "completion_cap_probability": probability(lambda packet: not packet["ended"]),
                "mean_reference": results["authored_reference_points"],
                "net_simulated_return": results["net"],
            }
    return summaries


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("directory", type=Path)
    cli.add_argument("--score", action="store_true")
    args = cli.parse_args()
    print(json.dumps(score(args.directory) if args.score else bundle(args.directory)[0], indent=2, ensure_ascii=False))
