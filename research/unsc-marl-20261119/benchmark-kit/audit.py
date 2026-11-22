"""Audit finite workshop designs under synchronous, lossless communication."""
import argparse
from collections import defaultdict
from fractions import Fraction
import itertools
import json
from pathlib import Path


def load_case(path):
    case = json.loads(path.read_text())
    archive = json.loads((path.parent / case["source_task"]).read_text())
    by_id = {row["id"]: row for row in archive["evidence"]}
    case["evidence"] = [by_id[key] for key in case["source_ids"]]
    roles, signals, answers = case["roles"], case["signals"], case["answers"]
    if not roles or len(set(roles)) != len(roles) or len(set(answers)) != len(answers):
        raise ValueError("Use unique roles and answer labels")
    for s in signals:
        if s["owner"] not in roles or len(set(s["values"])) != len(s["values"]) or len(s["values"]) < 2:
            raise ValueError("Invalid private signal")
    if len({s["field"] for s in signals}) != len(signals):
        raise ValueError("Signal fields must be unique")
    for sender, receiver in case["edges"]:
        if sender not in roles or receiver not in roles:
            raise ValueError("Unknown endpoint")
    worlds = list(itertools.product(*(s["values"] for s in signals)))
    if len(worlds) != len(case["gold"]) or any(not row or not set(row) <= set(answers) for row in case["gold"]):
        raise ValueError("Every world needs at least one legal answer")
    return case, worlds


def audit(case, worlds, rounds):
    roles = case["roles"]
    visible = {r: {i for i, s in enumerate(case["signals"]) if s["owner"] == r} for r in roles}
    rows = []
    for t in range(rounds + 1):
        fields = sorted(visible[roles[0]])
        groups = defaultdict(list)
        for i, world in enumerate(worlds):
            groups[tuple(world[j] for j in fields)].append(i)
        best = 0
        witness = None
        for ids in groups.values():
            best += max(sum(a in case["gold"][i] for i in ids) for a in case["answers"])
            if witness is None and not set.intersection(*(set(case["gold"][i]) for i in ids)):
                witness = [{"cards": worlds[i], "acceptable": case["gold"][i]} for i in ids]
        rows.append({"rounds": t, "chair_fields": fields, "ceiling": str(Fraction(best, len(worlds))),
                     "ambiguous_class": witness})
        after = {r: set(v) for r, v in visible.items()}
        for sender, receiver in case["edges"]:
            after[receiver].update(visible[sender])
        visible = after
    return rows


def oracle(case, world):
    # Independently encode the natural-language rules of the two example cards.
    if case["family"] == "mali-experts-2023":
        return {world[0]} if world[0] == world[1] else {"impasse"}
    if case["family"] == "myanmar-9231":
        allowed = {"both": {"early", "late"}, "early only": {"early"}, "late only": {"late"}}
        return allowed[world[0]] & allowed[world[1]] or {"reschedule"}
    raise ValueError("No independent oracle registered for this family")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path)
    parser.add_argument("--view", metavar="ROLE")
    parser.add_argument("--world", type=int, default=0)
    parser.add_argument("--rounds", type=int, default=2)
    parser.add_argument("--check-gold", action="store_true")
    args = parser.parse_args()
    case, worlds = load_case(args.case)
    if args.rounds < 0 or not 0 <= args.world < len(worlds):
        parser.error("Invalid round count or world index")
    if args.check_gold:
        for world, gold in zip(worlds, case["gold"]):
            if oracle(case, world) != set(gold):
                raise ValueError(f"Gold differs from mechanism for {world}")
    if args.view:
        if args.view not in case["roles"]:
            parser.error("Unknown role")
        result = {k: case[k] for k in ("scope", "question", "answers", "evidence", "roles", "edges")}
        result["deliverable"] = (
            "Submit one allowed action and a short chair's record. Give the action, next step, "
            "both card holders' relevant positions or availability, the decisive overlap or conflict, "
            "and the source and limits of authority. Mark unavailable evidence explicitly."
        )
        result["role"] = args.view
        result["cards"] = {s["field"]: worlds[args.world][i] for i, s in enumerate(case["signals"])
                           if s["owner"] == args.view}
    else:
        result = audit(case, worlds, args.rounds)
    print(json.dumps(result, indent=2))
