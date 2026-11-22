"""Export blinded review packets, compare locked readings, or score resolved verdicts."""
import argparse
from collections import Counter
from pathlib import Path

import evaluate as e
import report


def packets(records):
    cases, episodes = report.validate_episodes(records)
    out = {"final": {}, "process": {}}
    links = {}
    for key, row in episodes.items():
        name, arm, order = key.split("/")
        case = cases[name]
        calls = e.validate_calls(case, arm, int(order), row["calls"])
        final = e.final_packet(case, calls)
        process = e.process_packet(case, calls)
        out["final"][final["id"]] = e.judge.request(final)
        out["process"][process["id"]] = process
        links[key] = {"final": final["id"], "process": process["id"]}
    return {mode: dict(sorted(items.items())) for mode, items in out.items()}, links


def combine(records, marks):
    queue, links = packets(records)
    e.require(set(marks) == set(queue), "Both verdict modes are required")
    for mode, items in queue.items():
        e.require(set(marks[mode]) == set(items), f"Missing or unexpected {mode} verdicts")
    return [{"id": row["id"], "calls": row["calls"], **{
        mode: marks[mode][key] for mode, key in links[row["id"]].items()
    }} for row in records]


def extract_marks(records):
    marks = {"final": {}, "process": {}}
    for row in records:
        mode, verdict = row["mode"], row["verdict"]
        key = verdict["id"]
        e.require(key not in marks[mode] or marks[mode][key] == verdict,
                  "Identical packets have differing verdicts. Resolve them before exporting.")
        marks[mode][key] = verdict
    return marks


def extract(records):
    _, links = packets(records)
    return extract_marks({"mode": mode, "verdict": row[mode]}
                         for row in records for mode in links[row["id"]])


def compare(records, left, right):
    first = report.run(combine(records, left))
    second = report.run(combine(records, right))
    keys = ("criterion", "guard", "release", "released_70", "process_rating", "packet_unique_idea_count")
    tallies = {key: Counter(total=0, agreed=0) for key in keys}
    guard_confusion = Counter()
    disagreements = []

    def compare_field(kind, packet, field, a, b):
        tallies[kind]["total"] += 1
        tallies[kind]["agreed"] += a == b
        if a != b:
            disagreements.append({"kind": kind, "packet": packet, "field": field,
                                  "first": a, "second": b})

    for packet, a in left["final"].items():
        b = right["final"][packet]
        guard_a, guard_b = a["guard"]["status"], b["guard"]["status"]
        guard_confusion[f"{guard_a}/{guard_b}"] += 1
        compare_field("guard", packet, "guard", guard_a, guard_b)
        by_id = e.judge.by_id(b["units"])
        for item in a["units"]:
            field = item["id"]
            compare_field("criterion", packet, field, item["status"], by_id[field]["status"])

    queue, _ = packets(records)
    for packet, a in left["process"].items():
        b = right["process"][packet]
        by_id = e.judge.by_id(b["ratings"])
        for item in a["ratings"]:
            field = item["id"]
            if field in e.PROCESS["interactions"]:
                turns = queue["process"][packet]["turns"]
                if 0 not in turns[1]["visible"] or turns[0]["speaker"] == turns[1]["speaker"]:
                    continue
            compare_field("process_rating", packet, field, item["points"], by_id[field]["points"])
        compare_field("packet_unique_idea_count", packet, "unique_ideas", len(a["ideas"]), len(b["ideas"]))

    for episode, a in first["episodes"].items():
        b = second["episodes"][episode]
        compare_field("release", episode, "release", a["final"]["release"], b["final"]["release"])
        compare_field("released_70", episode, "released_70",
                      a["final"]["released_70"], b["final"]["released_70"])

    def direction(delta):
        return (delta > 0) - (delta < 0)

    def outcome(a, b):
        return {"first": a, "second": b, "same_direction": direction(a) == direction(b)}

    comparisons = {}
    for track, a in first["tracks"].items():
        b = second["tracks"][track]
        comparisons[track] = {}
        for baseline in ("independent", "solo"):
            metric = f"peer_minus_{baseline}"
            comparisons[track][metric] = {
                "macro": outcome(a[f"{metric}_macro"], b[f"{metric}_macro"]),
                "family_by_order": {
                    family: {order: outcome(delta, b["families"][family][f"{metric}_by_order"][order])
                             for order, delta in scores[f"{metric}_by_order"].items()}
                    for family, scores in a["families"].items()
                },
                "order_robust_family_wins": {
                    "first": a[f"order_robust_family_wins_over_{baseline}"],
                    "second": b[f"order_robust_family_wins_over_{baseline}"],
                },
            }
    return {"counts": tallies, "guard_confusion": guard_confusion, "disagreements": disagreements,
            "outcome_sensitivity": comparisons}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("packets", "extract", "extract-marks", "compare", "apply"))
    parser.add_argument("records", type=Path)
    parser.add_argument("marks", nargs="*", type=Path)
    args = parser.parse_args()
    n = {"packets": 0, "extract": 0, "extract-marks": 0, "compare": 2, "apply": 1}[args.mode]
    if len(args.marks) != n:
        parser.error(f"{args.mode} requires {n} marks files")
    records = report.load(args.records)
    marks = [e.read(path) for path in args.marks]
    if args.mode == "packets":
        e.emit(packets(records)[0])
    elif args.mode == "extract":
        e.emit(extract(records))
    elif args.mode == "extract-marks":
        e.emit(extract_marks(records))
    elif args.mode == "compare":
        e.emit(compare(records, *marks))
    else:
        e.emit(report.run(combine(records, *marks)))


if __name__ == "__main__":
    main()
