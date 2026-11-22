"""Run a fitted UN workshop team with role-local replies and a checked record compiler."""
import argparse
from dataclasses import dataclass
from functools import cache
from hashlib import sha256
import json
from pathlib import Path
import random
import sys
from uuid import uuid4

import numpy as np

HERE = Path(__file__).resolve().parent
BANK = HERE.parent
sys.path.insert(0, str(BANK / "source-aware"))
import chooser
import source_aware as fit

score, g = fit.score, fit.game
r, e = score.r, score.e
MODES = ("auto", "former", "aware", "former-always", "fixed", "silent")
PROFILES = {"even": (.9, .9, .9), "access-weak": (.9, .8, .35), "first-weak": (.35, .93, .72)}
State = tuple[int, int, int]


@dataclass(frozen=True)
class Question:
    run: str
    turn: int
    role: int
    public_state: State
    remaining: int


@dataclass(frozen=True)
class AttestedReply:
    question: Question
    bit: int


class Desk:
    """An addressed adapter sees the public question and its own case card."""

    def __init__(self, role, case, private_bit, decide, generate):
        self.role = role
        self.case = case
        self.bit = private_bit
        self.decide = decide
        self.generate = generate

    def answer(self, question):
        if question.role != self.role:
            raise ValueError("Question addressed to another desk")
        want = self.decide(question.public_state, question.remaining, self.role, self.bit)
        if not want:
            return None, "withheld"
        request = r.w.archived.request(self.case, self.role, self.bit, question.public_state)
        try:
            reply = self.generate(request)
        except TimeoutError:
            return None, "timed_out"
        expected = "Y" if self.bit == self.case["packages"]["A"][self.role] else "N"
        if (not isinstance(reply, dict) or reply.get("termination") != "complete"
                or reply.get("text") != expected):
            return None, "rejected"
        return AttestedReply(question, self.bit), "attested"


def admit(question, receipt):
    if receipt is None:
        return question.public_state
    if (receipt.question != question or type(receipt.bit) is not int or receipt.bit not in (0, 1)
            or question.public_state[question.role] != -1):
        raise ValueError("Receipt does not match an open addressed question")
    return g.write_bit(question.public_state, question.role, receipt.bit)


def teams(menu, rates, values, heads):
    former = score.arms_for(menu, rates)
    new = fit.deploy(menu, rates, values, heads)
    return {"former": former["learned"], "aware": new, "former-always": former["always_reply"],
            "fixed": former["fixed"], "silent": former["silent"]}


@cache
def loaded():
    bank = e.read(BANK / "source-aware" / "results.json")
    heads = {int(h): tuple(tuple(np.array(x) for x in a) for a in pair) for h, pair in bank["heads"].items()}
    values = {key: tuple(item["packet_values"]) for key, item in bank["evaluation"].items()}
    return heads, values


def choose(arm, context, rates, cap, mode, proposals):
    heads, values = loaded()
    public_menu = context[1]
    actors = teams(public_menu, rates, values[arm], heads)
    if mode != "auto":
        return mode, *actors[mode]
    # Enumerate the public prior and value function, without passing the actual world.
    if r.admit(arm, proposals) != r.admit(arm, r.direct(arm)):
        raise ValueError("Automatic selection requires the source fields covered by the packet contract")
    evaluate = score.documentary(arm, proposals, context)
    candidates = ("former", "aware", "silent")
    forecast = {name: chooser.measure(public_menu, evaluate, rates, cap, actors[name])["net"]
                for name in candidates}
    selected = max(candidates, key=lambda name: (forecast[name], name == "silent"))
    return selected, *actors[selected]


def fixture(case):
    def generate(request):
        # This adapter emulates the declared bit. It is also useful for transport tests.
        item = json.loads(request["messages"][-1]["content"])
        local = next(role for role in case["roles"] if role["name"] == item["role"])
        field = local["field"]
        value = item["simulated_requirement"].removeprefix(f"The {field} must be ").removesuffix(".")
        term = item["package_a_term"].removeprefix(f"The {field} is ").removesuffix(".")
        assert value in local["values"] and term in local["values"]
        return {"text": "Y" if value == term else "N", "termination": "complete"}
    return generate


def archived(arm):
    if arm == "mali":
        p = r.OLD / "evidence" / "episodes.jsonl"
        items = [json.loads(line) for line in p.read_text().splitlines()]
        archived = [row for item in items for row in item["steps"] if "request" in row]
    else:
        p = r.cy.RUN / "trace.jsonl"
        items = [json.loads(line) for line in p.read_text().splitlines()]
        archived = [row for row in items if row["stage"] == "delegate" and "request" in row]
    manifest = e.read(p.parent / "complete.json")
    if manifest[p.name] != sha256(p.read_bytes()).hexdigest():
        raise ValueError("Archived dialogue bytes have changed")
    index = {e.checksum(x["request"]): x["reply"] for x in archived}

    def generate(request):
        key = e.checksum(request)
        if key not in index:
            raise ValueError("No native reply for this exact addressed request")
        return index[key]

    return generate


def finalize(arm, case, menu, state, proposals):
    admitted, admission = r.admit(arm, proposals)
    proof = r.cy.proof(case, state)
    decision = g.terminal(menu, state)[0]
    known = r.w.renderer.public_conditions(case, state)
    scope = ("This workshop creates no authority over sanctions or expert mandates." if arm == "mali" else
             "This workshop changes neither the Council resolution, the mandate nor the parties' positions.")
    final = f"Decision: {decision}\n\nFictional briefing. {known} {proof} {scope}"
    if admitted:
        final += "\n\n" + " ".join(admitted.values())
    return final, admission


def chair_loop(menu, cap, ask, contact, run):
    state = g.EMPTY
    public = []
    for turn in range(cap):
        left = cap - turn
        role = ask(state, left)
        if role is None:
            break
        if type(role) is not int or role not in range(len(state)) or state[role] >= 0:
            raise ValueError("Chair requested an ineligible role")
        question = Question(run, turn, role, state, left)
        receipt = contact(question)
        after = admit(question, receipt)
        public.append({"turn": turn, "remaining": left, "role": role, "before": state,
                       "received": receipt.bit if receipt is not None else None, "after": after})
        state = after
    return state, g.terminal(menu, state)[0], public


def run(arm, private, rates, cap, mode, generation, dropped=(), invalid=(), actual=None, seed=0):
    template = r.load(arm)
    case, menu = template[:2]
    if type(cap) is not int or cap not in (2, 3):
        raise ValueError("Budget is two or three questions")
    if len(private) != 3 or any(type(bit) is not int or bit not in (0, 1) for bit in private):
        raise ValueError("A workshop needs one binary private card per desk")
    if len(rates) != 3 or any(not 0 <= rate <= 1 for rate in rates):
        raise ValueError("Provide three public delivery rates")
    if actual is not None and (len(actual) != 3 or any(not 0 <= rate <= 1 for rate in actual)):
        raise ValueError("Provide three actual delivery rates")
    if any(type(turn) is not int or turn not in range(cap) for turn in (*dropped, *invalid)):
        raise ValueError("Injected turn must be within the question budget")
    proposals = r.direct(arm)
    selected, ask, send = choose(arm, template, rates, cap, mode, proposals)
    compiler = {"arm": selected, "budget": cap, "public_rates": rates}
    run_id = uuid4().hex
    if callable(generation):
        base_generate, adapter_name = generation, "callback"
    elif generation == "archive":
        base_generate, adapter_name = archived(arm), generation
    elif generation == "fixture":
        base_generate, adapter_name = fixture(case), generation
    else:
        raise ValueError("Unknown delegate adapter")
    # Fault effects and attempts exist in the simulator's receipt accounting.
    # Only a valid receipt can go to the chair.
    accounting = []
    generator = random.Random(seed)

    def contact(question):
        def generate(request):
            if question.turn in invalid:
                return {"text": "Y or N", "termination": "complete"}
            return base_generate(request)

        desk = Desk(question.role, case, private[question.role], send, generate)
        receipt, status = desk.answer(question)
        blind_drop = actual is not None and generator.random() >= actual[question.role]
        if receipt is not None and (question.turn in dropped or blind_drop):
            receipt, status = None, "dropped"
        accounting.append(status)
        return receipt

    state, cert, log = chair_loop(menu, cap, ask, contact, run_id)
    final, source_fields = finalize(arm, case, menu, state, proposals)
    if len(final.split()) > (225 if arm == "mali" else 150):
        raise ValueError("Composed record exceeds the packet word cap")
    attempts = sum(status != "withheld" for status in accounting)
    return {"case": arm, **compiler, "adapter": adapter_name, "decision": cert, "state": state,
            "public_trace": log, "source_admission": source_fields, "record": final,
            "accounting": {"queries": len(log), "attempts": attempts, "statuses": accounting,
                           "cost": round(len(log) * fit.core.QUERY_COST + attempts * fit.core.SEND_COST, 8)}}


def digits(value):
    if len(value) != 3 or set(value) - {"0", "1"}:
        raise argparse.ArgumentTypeError("Use three binary digits such as 010")
    return tuple(map(int, value))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=r.ARMS)
    parser.add_argument("--private", required=True, type=digits)
    parser.add_argument("--policy", choices=MODES, default="auto")
    parser.add_argument("--budget", type=int, choices=(2, 3), default=2)
    parser.add_argument("--profile", choices=PROFILES, default="even")
    parser.add_argument("--deliver", choices=PROFILES, help="Simulate this physical delivery profile")
    parser.add_argument("--adapter", choices=("fixture", "archive"), default="fixture")
    parser.add_argument("--drop", type=int, action="append", default=[])
    parser.add_argument("--invalid", type=int, action="append", default=[])
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    e.emit(run(args.case, args.private, PROFILES[args.profile], args.budget, args.policy,
               args.adapter, args.drop, args.invalid, PROFILES.get(args.deliver), args.seed))
