"""Validate source spans and evaluate the frozen policies on both writer banks."""
from fractions import Fraction
from itertools import product
import json

from collect_native import HERE, RELEASE, TEAM, blocks, collector, fixture, load, locked, read

judge = load("native_team_chair_judge", RELEASE / "judge_score.py")
BINARY = (0, 1)


def packet(key, row):
    evidence = blocks(*row["receipts"])
    available = evidence + [r for r in fixture.RELATIONS if set(r["requires"]) <= set(row["receipts"])]
    return {"id": key, "rubric": available, "answer": row["reply"]["text"], "evidence": evidence}


def grade(key, row, verdict):
    reading = packet(key, row)
    sources = judge.by_id(reading["evidence"])
    assert set(verdict) == {"id", "units", "guard"} and verdict["id"] == key
    by_id = judge.by_id(verdict["units"])
    assert set(by_id) == set(judge.by_id(reading["rubric"]))
    points = 0
    uncertain = 0
    text = reading["answer"]
    for rule in reading["rubric"]:
        unit = by_id[rule["id"]]
        assert set(unit) == {"id", "status", "source", "response", "reason"}
        assert unit["status"] in {"met", "unmet", "uncertain"}
        judge.citations(unit["source"], sources)
        judge.span(unit["response"], text, unit["status"] != "unmet")
        judge.reason(unit)
        if unit["status"] == "met":
            required = set(rule.get("requires", [rule["id"]]))
            assert required <= {citation["block"] for citation in unit["source"]}
            points += rule["weight"]
        elif unit["status"] == "uncertain":
            uncertain += rule["weight"]
    guard = verdict["guard"]
    assert set(guard) == {"status", "response", "source", "reason"}
    assert guard["status"] in {"clear", "uncertain", "failed"}
    judge.citations(guard["source"], sources)
    judge.span(guard["response"], text, guard["status"] != "clear")
    judge.reason(guard)
    assert guard["status"] == "clear" or guard["source"]
    words = len(text.split())
    blockers = []
    if guard["status"] != "clear":
        blockers.append("guard_" + guard["status"])
    if row["reply"]["termination"] != "complete":
        blockers.append("termination_" + row["reply"]["termination"])
    if not 0 < words <= fixture.CASE["word_cap"]:
        blockers.append("word_count")
    covered = [k for k, u in by_id.items() if u["status"] == "met"]
    release = points if not blockers else 0
    return {"raw_70": [points, points + uncertain], "released_70": release,
            "released_relationship": sum(r["weight"] for r in fixture.RELATIONS
                                         if release and r["id"] in covered),
            "blockers": blockers, "words": words, "met": covered}


def payoff(bank, q_first, q_reply, price, send, reply):
    released = relationship = Fraction(0)
    for view, first, last in product(BINARY, repeat=3):
        front = q_first * send[view]
        probability = (front if first else 1-front) * (q_reply if last else 1-q_reply) / 2
        observation = view if first else None
        action = reply[observation if first else 2] if last else None
        row = bank[f"{observation}/{action}"]
        released += probability * row["released_70"]
        relationship += probability * row["released_relationship"]
    cost = Fraction(price * sum(send), 2)
    return {"utility": float(released-cost), "release": float(released),
            "relationship": float(relationship), "cost": float(cost),
            "send": list(send), "reply_received_r_g_missing": list(reply)}


def evaluate(bank, team):
    out = {}
    for trial in team["test"]:
        if trial["family"] != "afghanistan":
            continue
        first, reply, price = (trial[name] for name in ("q_first", "q_reply", "cost"))
        key = f"{first}/{reply}/{price}"
        learned = trial["policies"]["learned"]
        observation_ids = team["verified_observations"][1][:2]
        assert observation_ids == [2, 1]
        choices = tuple(1 - learned["reply"][i] for i in (*observation_ids, 0))
        send = learned["send"][:2]

        def pay(transmit, routes):
            return payoff(bank, Fraction(str(first)), Fraction(str(reply)), price, transmit, routes)

        candidates = [(s, r) for s in product(BINARY, repeat=2) for r in product(BINARY, repeat=3)]
        row = {
            "learned_both": pay(send, choices),
            "learned_sender_fixed_unama": pay(send, (1, 1, 1)),
            "learned_sender_best_arrival_reply": max((pay(send, r) for _, r in candidates if r[0] == r[1]),
                                                     key=lambda p: p["utility"]),
            "never_send_best_reply": max((pay((0, 0), (x, x, x)) for x in BINARY),
                                         key=lambda p: p["utility"]),
            "best_arrival_only": max((pay(s, r) for s, r in candidates if r[0] == r[1]),
                                     key=lambda p: p["utility"]),
            "best_content_aware": max((pay(s, r) for s, r in candidates), key=lambda p: p["utility"]),
        }
        assert key not in out or row == out[key]
        out[key] = row
    assert len(out) == 48
    summary = {name: {field: round(sum(row[name][field] for row in out.values()) / len(out), 8)
                      for field in ("utility", "release", "relationship", "cost")}
               for name in next(iter(out.values()))}
    summary["learned_vs_best_arrival"] = {
        "wins": sum(r["learned_both"]["utility"] > r["best_arrival_only"]["utility"] for r in out.values()),
        "ties": sum(r["learned_both"]["utility"] == r["best_arrival_only"]["utility"] for r in out.values()),
        "losses": sum(r["learned_both"]["utility"] < r["best_arrival_only"]["utility"] for r in out.values()),
    }
    return {"summary": summary, "conditions": out}


def run():
    spec = locked()
    outputs = read(HERE / "verified.json")["outputs"]
    marks = read(HERE / "marks.json")
    assert set(marks) == set(outputs) == set(spec["requests"])
    assert all(row["receipts"] == spec["requests"][key]["receipts"] for key, row in outputs.items())
    live = {key: grade(key, row, marks[key]) for key, row in outputs.items()}
    reference = {key: {"released_70": row["grade"]["released_70"],
                       "released_relationship": row["grade"]["sections"]["relation"]}
                 for key, row in fixture.cases()[0].items()}
    team = read(TEAM / "results.json")
    return {"pins": {p.name: collector.sha(p) for p in
                     (HERE / "plan.json", HERE / "verified.json", HERE / "marks.json", HERE / "score.py")},
            "live_grades": live, "live": evaluate(live, team), "authored": evaluate(reference, team)}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
