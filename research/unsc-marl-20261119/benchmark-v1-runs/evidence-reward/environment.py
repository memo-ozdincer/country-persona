"""One-turn public requests with role-local pass decisions."""
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
sys.path.insert(0, str(RUNS / "source-bound-chair"))
import signed_coverage as old

CHAIR, E = old.chair, old.e
ROLES = old.ROLES
ACTIONS = ("silence", "sign", "mandate_target", "mandate_other")
COSTS = {"sign": .035, "mandate_target": .10, "mandate_other": .10}
ASK = .04
BONUS = .5


def menu_from_synthetic(proposals):
    return [{"id": p["package"], **dict(w.split(" is ", 1) for w in p["proposal"].split("; "))}
            for p in proposals]


def options(menu, requirement):
    field, value = requirement
    return {r["id"] for r in menu if r[field] == value}


def all_requirements(menu):
    return [(field, value) for field in menu[0] if field not in {"id", "text"}
            for value in sorted({r[field] for r in menu})]


def state(menu, log):
    by_role = defaultdict(list)
    for row in log:
        by_role[row["role"]].append(row)
    candidates = {}
    for role in ROLES:
        possible = all_requirements(menu)
        candidates[role] = [r for r in possible if all(
            set(q.get("accepts", ())) <= options(menu, r)
            and not set(q.get("excludes", ())) & options(menu, r) for q in by_role[role]
        )]
        assert candidates[role]
    ledger = CHAIR.readout("ABCD", ROLES, log)
    decision = next(iter(ledger["verified_options"]), None) if ledger["state"] == "AGREEMENT_POSSIBLE" else (
        "I" if ledger["state"] == "IMPASSE" else "U")
    assert decision is not None
    return {"decision": decision, "known": sum(len(x) == 1 for x in candidates.values()),
            "candidates": candidates}


def revealed(menu, log, action, recipient, query, requirement):
    accepts = options(menu, requirement)
    if action == "sign":
        announcement = old.claim("response", recipient, query in accepts, query)
    else:
        announcement = {"id": "response", "role": recipient, "accepts": sorted(accepts),
                        "excludes": sorted(set("ABCD") - accepts)}
    return state(menu, [*log, announcement])


def outcome(row, cost=0):
    proof = row["decision"] != "U"
    return [float(proof), float(proof and row["known"] == 2), cost]


def utility(metrics, bonus):
    decision, ready, cost = metrics
    return decision + bonus * ready - cost


def expected_after(before, after, delivery, cost):
    return [delivery * a + (1-delivery) * b for b, a in zip(before[:2], after[:2], strict=True)] + [cost]


def records():
    roster = old.SIGNED / "roster.json"
    raw = E.read(roster)
    cases = E.cases()
    proof_archive = E.read(RUNS / "source-bound-chair/replay.json")["records"]
    actual_held = {}
    for key, row in proof_archive.items():
        case = cases[key.split("/")[0]]
        for d in row["declarations"]:
            label = ROLES[case["roles"].index(d["role"])]
            claim = tuple(next(iter(d["requirement"].items())))
            assert actual_held.setdefault((case["id"], label), claim) == claim
    for split, rows in raw.items():
        for row in rows:
            inputs = json.loads(row["messages"][1]["content"])
            named = inputs["you"]
            query = row["target"]
            case_id = row["id"].split("/")[0]
            menu = menu_from_synthetic(inputs["possible_packages"]) if split == "train" else cases[case_id]["options"]
            log = old.initial(inputs["public_claims"])
            before = state(menu, log)
            worlds = {}
            facts = {}
            for act in ACTIONS[1:]:
                role = ROLES[1 - ROLES.index(named)] if act == "mandate_other" else named
                worlds[act] = {req: revealed(menu, log, act, role, query, req)
                               for req in before["candidates"][role]}
                if split == "held":
                    truth = actual_held[case_id, role]
                    assert truth in worlds[act]
                    facts[act] = truth
                    assert worlds[act][truth]["decision"] in [*row["gold"], "U"]
            field, value = inputs["my_full_fictional_requirement"].split(" must be ", 1)
            assert (field, value) in before["candidates"][named]
            if split == "held":
                assert facts["sign"] == (field, value)
            yield split, {"id": row["id"], "delivery": row["delivery"], "before": before, "named": named,
                          "worlds": worlds, "truth": facts}


def exact(row, bonus, available=ACTIONS):
    before = outcome(row["before"])
    projection = {"silence": utility(before, bonus)}
    admitted = {}
    for action in available[1:]:
        replies = row["worlds"][action]
        reward = {}
        for requirement, after in replies.items():
            metrics = expected_after(before, outcome(after), row["delivery"], ASK + COSTS[action])
            pass_metrics = before[:2] + [ASK]
            reward[requirement] = (metrics if utility(metrics, bonus) > utility(pass_metrics, bonus) + 1e-12
                                   else pass_metrics)
        projection[action] = sum(utility(m, bonus) for m in reward.values()) / len(reward)
        if row["truth"]:
            admitted[action] = reward[row["truth"][action]]
    action = max(available, key=projection.get)
    return {"action": action, "expected": before if action == "silence" else admitted.get(action),
            "projected_utility": projection}


def evaluate():
    arms = {
        "sign_decision_reward": (0., ACTIONS[:2]),
        "sign_evidence_reward": (BONUS, ACTIONS[:2]),
        "expanded_decision_reward": (0., ACTIONS),
        "target_mandate_and_evidence_reward": (BONUS, ACTIONS[:3]),
        "expanded_evidence_reward": (BONUS, ACTIONS),
    }
    rows = {row["id"]: {name: exact(row, bonus, allowed)
                        for name, (bonus, allowed) in arms.items()}
            for split, row in records() if split == "held"}
    assert len(rows) == 44
    summaries = {}
    for name in arms:
        items = [r[name] for r in rows.values()]
        total = [sum(item["expected"][i] for item in items) for i in range(3)]
        summaries[name] = {"actions": {a: sum(r["action"] == a for r in items) for a in ACTIONS},
                           "expected_proof": total[0], "expected_complete_record_opportunity": total[1],
                           "expected_cost": total[2], "mean_common_value": utility(total, BONUS) / len(items)}
    files = (Path(__file__), HERE / "protocol.md", old.SIGNED / "roster.json",
             RUNS / "source-bound-chair/replay.json", CHAIR.ROOT / "benchmark/release.json")
    return {"summary": summaries, "rows": rows, "bonuses": [0, BONUS], "send_cost": COSTS,
            "files_sha256": {str(p.relative_to(CHAIR.ROOT)): sha256(p.read_bytes()).hexdigest() for p in files}}


if __name__ == "__main__":
    E.emit(evaluate())
