"""Build signed reply prompts with private prose requirements and public proofs."""
from ast import literal_eval
from itertools import product
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "workshop-joint-action-fit"))
import environment as prior

E = prior.E
sys.path.insert(0, str(HERE.parents[1] / "crossbench"))
import decision_ledger as ledger

DEC = ("Y", "N", "P")
ROLES = ("Desk One", "Desk Two")
OPTS = tuple("ABCD")
COST = .035
DELIVERY = .8


def fact(owner, option, sign, key):
    return {"id": key, "role": owner, "accepts": [option] if sign else [],
            "excludes": [] if sign else [option]}


def decision(claims):
    state = ledger.readout(OPTS, ROLES, claims)
    if state["state"] == "AGREEMENT_POSSIBLE":
        return sorted(state["verified_options"])[0]
    return "I" if state["state"] == "IMPASSE" else "U"


def rendered(rows):
    return [
        f'{x["role"]} {"accepts " + x["accepts"][0] if x["accepts"] else "excludes " + x["excludes"][0]}.'
        for x in rows
    ]


def example(key, menu, cards, state, target, role, mode, family, delivery):
    true = [prior.allowed(menu, m) for m in cards]
    gold = sorted(true[0] & true[1] or {"I"})
    initial = decision(state)
    assert initial == "U" or initial in gold
    assert all(ledger.truthful_disclosure(f, true[ROLES.index(f["role"])]) for f in state)
    assert state and len({x["id"] for x in state}) == len(state)
    valid = target in true[role]
    effects, utilities = {}, []
    for label in DEC:
        if label == "P":
            effects[label] = {"decision": initial, "truthful": True, "new_proof": False, "wrong_commit": False}
            utilities.append(.15 if initial == "U" else 1.)
            continue
        semantic_truth = valid if label == "Y" else not valid
        after = decision([*state, fact(ROLES[role], target, label == "Y", "response")])
        effects[label] = {"decision": after, "truthful": semantic_truth,
                          "new_proof": semantic_truth and after != "U" and initial == "U",
                          "wrong_commit": after != "U" and after not in gold}
        base = .15 if initial == "U" else 1.
        value = (.15 if after == "U" else 1.) if semantic_truth else -1.
        # The local false-reply penalty applies even when delivery fails.
        utilities.append(base + delivery*(value-base)-COST if semantic_truth else -1.-COST)
    role_name = ROLES[role]
    fields = ", ".join(f"{k} must be {v}" for k, v in cards[role].items())
    system = (
        "You are a fictional workshop delegate replying to a one-package question. Use the menu and your "
        "private condition to decide whether the queried package is compatible with your own mandate. "
        "You may answer Y (compatible), N (incompatible), or P (pass). Pass when your signed claim cannot complete "
        "an agreement or an impasse given the public evidence, or when the outcome is already established. "
        "A joint agreement needs two yes statements on one package. An impasse needs an exclusion for every package. "
        "Never state another role's private condition. Output one letter only."
    )
    facts = [{"package": x["id"], "proposal": x["text"]} for x in menu]
    messages = [{"role": "system", "content": system}, {"role": "user", "content": json.dumps(
        {"you": role_name, "query_package": target, "my_full_fictional_requirement": fields,
         "possible_packages": facts, "public_claims": rendered(state)}, ensure_ascii=False)}]
    return {"id": key, "mode": mode, "family": family, "role": role, "gold": gold,
            "target": target, "truth": valid, "utility": utilities, "audit": effects,
            "messages": messages, "delivery": delivery}


def stimuli(tag, menu, cards, family, rate):
    left, right = [prior.allowed(menu, m) for m in cards]
    out = []
    for a, b in product(sorted(left), sorted(right)):
        if a == b:
            continue
        state = [fact(ROLES[0], a, True, "open1"), fact(ROLES[1], b, True, "open2")]
        out.extend(example(f"{tag}/two/{a}/{b}/{i}", menu, cards, state, t, i, "two_openings", family, rate)
                   for i, t in enumerate((b, a)))
    for i in (0, 1):
        local, other = (left, right) if i == 0 else (right, left)
        for label in sorted(other):
            others = set(OPTS) - {label}
            if others & left & right:
                continue
            state = [fact(ROLES[1-i], label, True, "open")]
            state += [fact(ROLES[0 if a not in left else 1], a, False, f"ex-{a}") for a in sorted(others)]
            out.append(example(f"{tag}/one/{label}/{i}", menu, cards, state, label, i, "last_unknown", family, rate))
            if label in local:
                both = [*state, fact(ROLES[i], label, True, "already")]
                out.append(example(f"{tag}/known/{label}/{i}", menu, cards, both, label, i, "certified", family, rate))
    return out


def development():
    rows = []
    for i, world in enumerate(prior.development()):
        packet = json.loads(world["chair"][0][1]["content"])
        menu = []
        for choice in packet["menu"]:
            key, text = choice.split(": ", 1)
            menu.append({"id": key, "text": text, **dict(t.split(" is ", 1) for t in text.split("; "))})
        cards = [literal_eval(s.split("My full requirement is ", 1)[1].split("}.", 1)[0] + "}")
                 for s in packet["public_notes"]]
        rows += stimuli(world["id"], menu, cards, "synthetic", (.39, .72, .94)[i % 3])
    return rows


def held():
    return [r for case in E.cases().values() if case["track"] == "workshop"
            for r in stimuli(case["id"], case["options"], case["membership"], case["family"], DELIVERY)]


def roster():
    train, test = development(), held()
    assert {r["family"] for r in train} == {"synthetic"}
    assert {r["family"] for r in test} == {"iraq", "syria"}
    assert len({r["id"] for r in train+test}) == len(train+test)
    return {"train": train, "held": test}


if __name__ == "__main__":
    E.emit(roster())
