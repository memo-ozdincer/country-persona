"""Native prompts and bounded team outcomes for the two workshop policies."""
import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "benchmark-v1"))
import evaluate as E

RESPONSES = ("K", "P", "W")
DECISIONS = ("A", "B", "C", "D", "I", "U")
COST = (0.04, 0.02, 0.0)


def allowed(menu, condition):
    return {r["id"] for r in menu if all(r[k] == v for k, v in condition.items())}


def blocks(menu):
    return [f'{r["id"]}: {r["text"]}' for r in menu]


def chair_prompt(menu, notes):
    return [{"role": "system", "content": "You are the workshop chair. Use only the reported constraints and endorsements. "
             "Choose a package only if both roles can accept it. Mark impasse if all packages are ruled out. "
             "Use unresolved for incomplete or conflicting evidence. Output exactly one letter from A, B, C, D, "
             "I (impasse), U (unresolved)."},
            {"role": "user", "content": json.dumps({"menu": blocks(menu), "public_notes": notes}, ensure_ascii=False)}]


def build(key, menu, local, opening_first, roles):
    a, b = [allowed(menu, card) for card in local]
    ids = [r["id"] for r in menu]
    proposal = next(p for p in ids if p in a)
    first, second = roles
    opening = f"{first}: My full requirement is {local[0]}. I can accept {proposal}."
    reply = (
        f"{second}: My full requirement is {local[1]}.",
        f"{second}: I can accept {proposal}.",
        f"{second}: I have no constraint or endorsement to add.",
    )
    def prompt():
        return [{"role": "system", "content": "You are the second workshop delegate. Respond as your own role. "
                 "K discloses your full requirement, P says you can accept the opening proposal, and W withholds. "
                 "Choose one action and output its letter only."},
                {"role": "user", "content": json.dumps({"menu": blocks(menu), "own_role": second,
                 "own_requirement": local[1], "opening_note": opening}, ensure_ascii=False)}]

    exact = a & b or {"I"}
    legal = [exact, {proposal} if proposal in b else set(), {"U"}]
    truth = [True, proposal in b, True]
    reward = [[(-1.0 if not true else (0.15 if d == "U" else 1.0) if d in ok else -1.0) - expense
               for d in DECISIONS] for ok, true, expense in zip(legal, truth, COST, strict=True)]
    return {"id": key, "order": opening_first, "opening_proposal": proposal, "proposal_compatible": proposal in b,
            "gold": sorted(exact), "certifiable": [sorted(answers) for answers in legal], "rewards": reward,
            "responder": prompt(), "chair": [chair_prompt(menu, [opening, text]) for text in reply]}


def development():
    worlds = []
    combos = (("format", ("written", "oral"), "review", ("one review", "two reviews")),
              ("venue", ("online", "onsite"), "timing", ("morning", "afternoon")),
              ("retention", ("six weeks", "ten weeks"), "access", ("open", "registered")),
              ("reporting", ("monthly", "quarterly"), "start", ("May", "October")))
    for index, (field, values, other, choices) in enumerate(combos):
        states = [(a, b) for a in values for b in choices]
        random.Random(512 + index).shuffle(states)
        menu = [{"id": label, field: a, other: b, "text": f"{field} is {a}; {other} is {b}"}
                for label, (a, b) in zip(DECISIONS[:4], states, strict=True)]
        cards = [({field: values[0]}, {field: values[0]}), ({field: values[0]}, {field: values[1]}),
                 ({field: values[1]}, {other: choices[0]}), ({field: values[1]}, {other: choices[1]})]
        for j, pair in enumerate(cards):
            order = (index + j) % 2
            worlds.append(build(f"synthetic-{index}-{j}", menu, pair[::1 if order == 0 else -1],
                                order, ("Opening reviewer", "Responding reviewer")))
    return worlds


def held():
    return [build(f'{row["id"]}/{order}', row["options"], row["membership"][::1 if order == 0 else -1],
                  order, row["roles"][::1 if order == 0 else -1])
            for row in E.cases().values() if row["track"] == "workshop" for order in (0, 1)]


def archived():
    baseline = HERE.parent / "syria-baseline"
    projected = HERE.parent / "syria-constraint-transport"
    source = E.read(baseline / "results.json")["episodes"]
    proc = E.read(projected / "results.json")["conditions"]
    rows = []
    for line in (baseline / "evidence/episodes.jsonl").read_text().splitlines():
        ep = json.loads(line)
        key = ep["id"]
        case, arm, order = key.split("/")
        if arm != "peer":
            continue
        menu = E.cases()[case]["options"]
        gold = ["I" if p == "IMPASSE" else p for p in E.cases()[case]["gold"]]
        paired = next(r for r in E.read(projected / "evidence/episodes.json") if r["episode"] == key)
        raw_notes = [r["text"] for r in ep["calls"][:2]]
        clean_notes = [paired["projected_text"], paired["note"]["response"]["text"]]
        for suffix, notes, state in (("raw", raw_notes, source[key]["notes"]["ledger"]["state"]),
                                     ("projected", clean_notes, proc[key]["details"]["notes"]["ledger"]["state"])):
            rows.append({"id": f"{key}/{suffix}", "chair": chair_prompt(menu, notes), "gold": gold,
                         "supported": ["I" if state == "IMPASSE" else "U"], "ledger_state": state})
    return rows


def roster():
    E.require(len((train := development())) == 16 and len((test := held())) == 8, "Unexpected world counts")
    actual = archived()
    assert len(actual) == 8
    assert all("syria" not in str(row).lower() and "iraq" not in str(row).lower() for row in train)
    return {"train": train, "held": test, "archived": actual}


if __name__ == "__main__":
    E.emit(roster())
