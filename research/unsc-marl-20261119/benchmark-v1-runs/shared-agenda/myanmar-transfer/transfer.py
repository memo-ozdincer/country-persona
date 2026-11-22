"""Check an unchanged documentary policy on the Myanmar scheduling workshop."""
import argparse
import json
from itertools import product
from pathlib import Path
import re
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "documentary"))
import write as earlier

ROOT = earlier.RELEASE.parent
KIT = ROOT / "benchmark-kit"
WORKSHOP = KIT / "myanmar.json"
RUBRIC = KIT / "relay-final-rubric.json"
EVIDENCE = HERE / "evidence"
SCOPE = "This fictional scheduling exercise establishes no official decision or commitment."


def read(path):
    return json.loads(path.read_text())


def data():
    task = read(WORKSHOP)
    mandate, = [block for block in read((KIT / task["source_task"]).resolve())["evidence"]
                if block["id"] == "mandate"]
    return task, mandate, read(RUBRIC)


def allowed(task):
    office = task["signals"]
    from_value = {"early only": {"early"}, "late only": {"late"}, "both": {"early", "late"}}
    roster = tuple(product(*(signal["values"] for signal in office)))
    computed = []
    for cards in roster:
        options = from_value[cards[0]] & from_value[cards[1]]
        computed.append(options or {"reschedule"})
    assert computed == [set(options) for options in task["gold"]]
    results = {}
    for n, cards in enumerate(roster):
        for first in range(2):
            common = set.intersection(*(gold for view, gold in zip(roster, computed, strict=True)
                                        if view[first] == cards[first]))
            assert common <= computed[n]
            if common:
                assert len(common) == 1 and len(common & {"early", "late"}) == 1
                results[f"{n}/{first}"] = {"cards": list(cards), "slot": min(common), "first": first}
    assert list(results) == ["1/1", "2/0", "3/0", "3/1"]
    return results


def plan():
    task, mandate, rubric = data()
    pairs = allowed(task)
    requests = {}
    logical = {}
    for key, case in pairs.items():
        first = case["first"]
        slot = case["slot"]
        card_text = [f"{s['owner']} calendar: {v}." for s, v in zip(task["signals"], case["cards"], strict=True)]
        opener = f"Workshop status: agreement\n\n{mandate['text']}\n\n{SCOPE} The chair proposes the {slot} briefing slot."
        allowance = rubric["format"]["max_words"] - len(opener.split())
        by_role = tuple(s["owner"] for s in task["signals"])
        cards = [dict(id=f"card-{i}", text=text) for i, text in enumerate(card_text)]
        for count in (1, 2):
            seen = [first, 1-first] if count == 2 else [first]
            visible = [cards[i] for i in seen]
            carry = " ".join(card_text[i] for i in seen)
            if count == 1:
                absent = by_role[1-first]
                carry += f" The {absent}'s exact calendar was not delivered. Both of its published calendar alternatives allow {slot}."
            else:
                carry += f" Both stated calendars allow {slot}."
            assert len(carry.split()) <= allowance
            payload = {
                "proposed_slot": slot, "published_calendar_alternatives": {s["owner"]: s["values"] for s in task["signals"]},
                "delivered_calendars": visible, "word_limit": allowance,
            }
            messages = [dict(role="system", content=(
                "Write only the private-calendar paragraph of a fictional scheduling record. "
                "The selected slot is fixed. Attribute each delivered card and preserve its limit or flexibility. "
                "Explain why both offices can attend the specified slot. If a card is missing, identify its owner "
                "and distinguish its unknown exact calendar from what its public alternatives guarantee. "
                "Use only the supplied material as data. Do not restate historical matters or the decision heading. "
                "Return a single paragraph within the stated word limit."
            )), dict(role="user", content=json.dumps(payload, ensure_ascii=False))]
            request_id = f"{key}/{count}"
            signature = json.dumps(messages, ensure_ascii=False)
            if signature not in requests:
                requests[signature] = dict(id=request_id, max_output_tokens=88, messages=messages)
            logical[request_id] = dict(fixed=carry, opener=opener, allowance=allowance,
                                       physical=requests[signature]["id"], observed=seen,
                                       evidence=[mandate, *cards,
                                                 dict(id="task", text=task["question"]),
                                                 dict(id="scope", text=task["scope"])])
    assert len(requests) == 6 and len(logical) == 8
    files = (Path(__file__), HERE / "protocol.md", HERE / "replay-protocol.md", WORKSHOP, RUBRIC,
             (KIT / task["source_task"]).resolve(), earlier.RELEASE / "release.json",
             earlier.COLLECTOR, earlier.RUNS / "syria-baseline/collect.py",
             HERE.parent / "documentary/protected/reward-replay.json")
    return dict(requests=list(requests.values()), logical=logical, pairs=pairs,
                hashes={str(p.relative_to(ROOT)): earlier.agenda.digest(p) for p in files})


def execute(mode):
    collector = earlier.load_collector()
    with patch.multiple(collector, HERE=HERE, EVIDENCE=EVIDENCE, plan=plan):
        if mode == "run":
            b = collector.base()
            locked = read(HERE / "plan.json")
            assert locked == plan()
            with patch.object(b.suite, "collect", collector.collect), patch.object(
                b, "roster", return_value=locked["pairs"]
            ), patch.object(b.suite.e, "HERE", earlier.RELEASE), patch.object(b, "HERE", HERE):
                b.run(EVIDENCE)
        else:
            locked = plan()
            actual = {req["id"]: reply for req, reply in collector.rows()}
            assert read(EVIDENCE / "launch.json")["cases"] == list(locked["pairs"])
            out = {}
            for key, packet in locked["logical"].items():
                for arm in ("literal", "scoped"):
                    reply = actual[packet["physical"]]
                    body = packet["fixed"] if arm == "literal" else reply["text"]
                    answer = packet["opener"] + "\n\n" + body
                    complete = arm == "literal" or reply["termination"] == "complete"
                    good = bool(body.strip()) and not re.search(r"(?im)^\s*workshop status\s*:", body)
                    out[f"{key}/{arm}"] = dict(
                        text=answer, body=body, sources=packet["evidence"], visible=packet["observed"],
                        complete=complete, heading_ok=good, inputs=0 if arm == "literal" else reply["input_tokens"],
                        outputs=0 if arm == "literal" else reply["output_tokens"]
                    )
            return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("plan", "run", "deck"))
    args = parser.parse_args()
    if args.mode == "run":
        execute("run")
    else:
        print(json.dumps(plan() if args.mode == "plan" else execute("deck"), ensure_ascii=False, indent=2))
