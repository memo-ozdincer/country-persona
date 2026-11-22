"""Evaluate expected documentary performance under the fixed source compiler."""
from functools import cache
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import check_record as review

r, e = review.r, review.e
g, core = r.w.game, r.w.fitted.core
HERE = Path(__file__).resolve().parent


def arms_for(menu, rates):
    raw = e.read(r.OLD.parent / "backward-results.json")["heads"]
    heads = {int(h): tuple(tuple(np.array(x) for x in a) for a in pair) for h, pair in raw.items()}
    ask, reply = r.w.fitted.deployed(menu, rates, heads)

    def always(*_):
        return True

    def fixed(state, _):
        return next((i for i, bit in enumerate(state) if bit < 0), None)

    return {"learned": (ask, reply), "always_reply": (ask, always),
            "fixed": (fixed, always), "silent": (lambda *_: None, always)}


def documentary(arm, proposals, context):
    case, menu, _, _, rubric, original = context

    @cache
    def evaluate(state, target):
        # The gold action is evaluator-only. The renderer receives the partial view.
        world = next(truth for truth in g.WORLDS if g.terminal(menu, truth)[0] == target)
        public = [item for item in original if item["id"] != "delivered"]
        public.append({"id": "delivered", "text": r.w.renderer.public_conditions(case, state)})
        with patch.object(r, "load", return_value=(case, menu, state, world, rubric, public)):
            doc_case, reply, _ = r.compose(arm, proposals)
        decision = g.terminal(menu, state)[0]
        packet = e.final_packet(doc_case, [{}, {}, reply])
        blocks = {b["id"]: b["text"] for b in packet["evidence"]}
        certified = decision != "UNRESOLVED"
        complete = -1 not in state
        if certified:
            allowed = g.options(menu, state)
            assert (not allowed and decision == "IMPASSE") or (len(allowed) == 1 and complete)
            assert decision == target
        if arm == "mali":
            evidence = {
                "disposition": (certified, ("status-638", "status-639", "checked-exclusions")),
                "action": (certified, ("checked-exclusions", "delivered", "menu")),
                "positions": (complete, ("french-uae", "russia", "delivered")),
                "open_issues": (True, ("status-638", "status-639", "delivered")),
                "authority": (True, ("scope", "status-638", "status-639")),
            }
        else:
            vote = arm != "cyprus-withheld"
            evidence = {
                "vote": (vote, ("vote",)),
                "mandate": (True, ("mandate",)),
                "positions": (vote, ("positions", "settlement")),
                "proof": (certified, ("delivered", "menu", "checked-exclusions")),
                "scope": (True, ("scope", "mandate")),
            }
        grades = {"id": packet["id"], "guard": {"status": "clear", "source": [], "response": "",
                    "reason": "Checked clauses and public proof are composed without free-form claims."},
                  "units": [{"id": key, "status": "met" if met else "unmet",
                    "response": reply["text"] if met else "",
                    "source": [{"block": label, "quote": blocks[label]} for label in cited] if met else [],
                    "reason": "Compiled criterion replay."} for key, (met, cited) in evidence.items()]}
        scored = e.final_score(doc_case, [{}, {}, reply], grades)
        assert scored["release"] == certified
        return scored["released_70"] / 70, certified, scored["strict"]

    return evaluate


def expected(menu, evaluate, rates, truth, cap, ask, reply):
    target = g.terminal(menu, truth)[0]

    @cache
    def walk(state, left):
        role = ask(state, left) if left else None
        if role is None:
            return np.array([*evaluate(state, target), 0., 0.])
        send = reply(state, left, role, truth[role])
        skip = walk(state, left - 1)
        if not send:
            return skip + np.array([0., 0., 0., 1., 0.])
        delivered = walk(g.write_bit(state, role, truth[role]), left - 1)
        return rates[role] * delivered + (1 - rates[role]) * skip + np.array([0., 0., 0., 1., 1.])

    return walk(g.EMPTY, cap)


def run():
    native = {x["arm"]: r.parse(x["reply"]) for x in review.rows("calls.jsonl")}
    result = {}
    for arm in r.ARMS:
        assert r.admit(arm, native[arm]) == r.admit(arm, r.direct(arm))
        context = r.load(arm)
        menu = context[1]
        evaluate = documentary(arm, native[arm], context)
        pivotal = e.read(HERE / "results.json")[f"{arm}/native"]["score"]
        assert evaluate(context[2], "IMPASSE")[0] == pivotal["released_70"] / 70
        rows = {}
        for rates in g.HELD:
            actors = arms_for(menu, rates)
            for cap in (2, 3):
                summary = {}
                for name, (ask, reply) in actors.items():
                    points, accepted, strict, queries, attempted = map(float, np.mean([
                        expected(menu, evaluate, rates, truth, cap, ask, reply) for truth in g.WORLDS], axis=0))
                    summary[name] = {"expected_released_70": 70 * points, "decision_accuracy": accepted,
                        "strict_rate": strict, "questions": queries, "attempted_replies": attempted,
                        "net": points - core.QUERY_COST * queries - core.SEND_COST * attempted}
                rows[f"{rates}/{cap}"] = summary
        result[arm] = rows
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
