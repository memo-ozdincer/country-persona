"""Run the frozen team on the Cyprus workshop and compare two writer inputs."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
from unittest.mock import patch

import numpy as np

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / "mali-three-role" / "team-return" / "language-witness"
sys.path.insert(0, str(OLD))
import witness as common

game, e = common.game, common.archived.E
RUN = HERE / "evidence"
RATES = (.9, .9, .9)


def setup():
    case = game.read(HERE / "case.json")
    menu = tuple(tuple(x) for x in case["packages"].values())
    assert game.shape(menu) == game.shape(common.load()[1])
    raw = game.read(OLD.parent / "backward-results.json")["heads"]
    heads = {int(h): tuple(tuple(np.array(x) for x in actor) for actor in pair) for h, pair in raw.items()}
    policy = common.fitted.deployed(menu, RATES, heads)
    return case, menu, *policy


def selected():
    _, menu, ask, gate = setup()
    for world in game.WORLDS:
        if common.oracle_trace(menu, ask, gate, world, False)[1] == "IMPASSE":
            return world
    raise ValueError("No two-reply impasse")


def proof(case, state):
    options = case["packages"]
    remaining = list(options)
    reasons = []
    for i, (role, bit) in enumerate(zip(case["roles"], state, strict=True)):
        if bit < 0:
            continue
        blocked = [name for name, opt in options.items() if opt[i] != bit]
        remaining = [name for name in remaining if name not in blocked]
        reasons.append(role["name"] + " excludes " + ", ".join(blocked) + ".")
    return " ".join(reasons) + " Compatible options after applying confirmed requirements: " + (
        ", ".join(remaining) + "." if remaining else "none.")


def public(case, state):
    return case["sources"] + [{"id": "scope", "text": case["scope"]},
        {"id": "menu", "text": " ".join(f"{name}: {common.renderer.describe(case, opt)}."
                                      for name, opt in case["packages"].items())},
        {"id": "delivered", "text": common.renderer.public_conditions(case, state)}]


TASK = (
    "Write a concise retrospective Council chair note, in 150 words or fewer. Begin with exactly "
    "Decision: A, Decision: B, Decision: C, Decision: D, Decision: IMPASSE, or Decision: UNRESOLVED. "
    "This line concerns only the fictional briefing. No surviving option means IMPASSE even if a condition "
    "is unknown. Use UNRESOLVED when at least one option survives and any requirement is unknown. "
    "Next state the admitted requirements, their exclusions, and any unknown role. Then state the draft, vote "
    "and renewal, the president's account of the parties, and the mandate's reach and limits."
)


def writer(case, state, compiled_proof):
    rows = public(case, state)
    if compiled_proof:
        rows = [*rows, {"id": "checked-exclusions", "text": proof(case, state)}]
    return {"messages": [
        {"role": "system", "content": "Use the supplied evidence only. Write the requested note in two short paragraphs after the decision line."},
        {"role": "user", "content": json.dumps({"task": TASK, "evidence": [
            {"id": r["id"], "text": r["text"]} for r in rows]}, ensure_ascii=False)}],
        "max_output_tokens": 280}


def execute(generate):
    case, menu, ask, gate = setup()
    world = selected()
    state = game.EMPTY
    for budget in (2, 1):
        role = ask(state, budget)
        if role is None:
            break
        send = gate(state, budget, role, world[role])
        row = {"stage": "delegate", "role": role, "before": state, "send": send}
        if send:
            request = common.archived.request(case, role, world[role], state)
            reply = generate(request)
            match = "Y" if world[role] == case["packages"]["A"][role] else "N"
            accepted = reply["text"] == match and reply["termination"] == "complete"
            if accepted:
                sign = case["packages"]["A"][role] if reply["text"] == "Y" else 1 - case["packages"]["A"][role]
                state = game.write_bit(state, role, sign)
            row.update(request=request, reply=reply, accepted=accepted)
        yield row | {"after": state}
    for kind in ("raw", "proof"):
        request = writer(case, state, kind == "proof")
        yield {"stage": "writer", "arm": kind, "state": state, "public_decision": game.terminal(menu, state)[0],
               "request": request, "reply": generate(request)}


def plan():
    case, menu, ask, gate = setup()
    world = selected()
    actions, outcome = common.oracle_trace(menu, ask, gate, world, False)
    assert len(actions) == 2 and all(wants for _, wants in actions) and outcome == "IMPASSE"
    state = game.EMPTY
    for role, _ in actions:
        state = game.write_bit(state, role, world[role])
    return {"world": world, "route": actions, "outcome": outcome,
            "public_proof": proof(case, state), "output_caps": [32, 32, 280, 280]}


def pins():
    sources = (Path(__file__), HERE / "case.json", HERE / "protocol.md", HERE / "plan.json",
               OLD.parent / "backward-results.json", OLD.parent / "backward.py", OLD.parent / "train.py",
               OLD / "witness.py", OLD.parent.parent / "live" / "live.py")
    return {str(p.relative_to(HERE.parent)): sha256(p.read_bytes()).hexdigest() for p in sources}


def collect(generate, directory):
    assert json.loads(json.dumps(plan())) == e.read(HERE / "plan.json")
    for line in execute(generate):
        common.archived.base.suite.append(directory / "trace.jsonl", line)
    (directory / "inputs.json").write_text(json.dumps(pins(), indent=2) + "\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("plan", "run"))
    if p.parse_args().mode == "plan":
        e.emit(plan())
    else:
        with patch.object(common.archived.base.suite, "collect", collect), patch.object(
                common.archived.base, "roster", return_value={"cyprus": None}):
            common.archived.base.run(RUN)
