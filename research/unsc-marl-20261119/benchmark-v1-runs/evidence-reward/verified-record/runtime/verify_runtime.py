"""Verify exact archived replay, fault handling and the runtime's public interface."""
from dataclasses import replace
from itertools import product
import json
from pathlib import Path
from unittest.mock import patch

import workshop as w

HERE = Path(__file__).resolve().parent
WITNESSES = (("mali", (0, 1, 0), "access-weak", "former", 56),
             ("cyprus", (0, 0, 1), "even", "auto", 70))


def rejects(fn):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError("Expected rejection")


def replay_witnesses():
    results = {}
    for case_id, world, profile, mode, score in WITNESSES:
        live = w.run(case_id, world, w.PROFILES[profile], 2, mode, "archive")
        assert json.loads(json.dumps(live)) == w.e.read(HERE / f"{case_id}-archive.json")
        assert live["record"] == w.e.read(w.BANK / "packets.json")[f"{case_id}/direct"]["answer"]
        archived_score = w.e.read(w.BANK / "results.json")[f"{case_id}/direct"]["score"]
        assert archived_score["released_70"] == score
        assert live["decision"] == "IMPASSE" and live["accounting"]["statuses"] == ["attested", "attested"]
        faults = {}
        for fault, turn in product(("dropped", "invalid"), (0, 1)):
            result = w.run(case_id, world, w.PROFILES[profile], 2, mode, "fixture",
                           **{("dropped" if fault == "dropped" else "invalid"): [turn]})
            assert result["decision"] == "UNRESOLVED"
            step = result["public_trace"][turn]
            assert step["received"] is None and step["before"] == step["after"]
            assert "private" not in result and "accounting" not in step
            faults[f"{fault}/{turn}"] = result["accounting"]
        results[case_id] = {"decision": live["decision"], "released_70": score, "fault_tests": faults}
    return results


def invalid_receipts():
    current = w.Question("run-1", 0, 1, (-1, -1, -1), 2)
    assert w.admit(current, w.AttestedReply(current, 1)) == (-1, 1, -1)
    assert w.admit(current, None) == (-1, -1, -1)
    for update in ({"run": "run-2"}, {"turn": 1}, {"role": 2},
                   {"public_state": (0, -1, -1)}, {"remaining": 1}):
        stale = replace(current, **update)
        rejects(lambda: w.admit(current, w.AttestedReply(stale, 1)))
    for bad in (-1, 2, True, "1"):
        rejects(lambda: w.admit(current, w.AttestedReply(current, bad)))
    return 9


def no_secret_prompt(arm):
    case, menu, *_ = w.r.load(arm)
    for role, own in product(range(3), (0, 1)):
        state = (-1, -1, -1)
        requests = []
        private_args = []
        q = w.Question("run", 0, role, state, 2)

        def record(req):
            requests.append(json.loads(req["messages"][-1]["content"]))
            return w.fixture(case)(req)

        def wants(*args):
            private_args.append(args)
            return True

        desk = w.Desk(role, case, own, wants, record)
        reply, status = desk.answer(q)
        assert status == "attested" and reply.bit == own
        assert private_args == [(state, 2, role, own)]
        prompt, = requests
        assert set(prompt) == {"role", "simulated_requirement", "package_a_term", "public_disclosed_requirements"}
        assert prompt["role"] == case["roles"][role]["name"] and prompt["public_disclosed_requirements"] == {}
        for i, card in enumerate(case["roles"]):
            if i != role:
                assert card["field"] not in prompt["simulated_requirement"]
        rejects(lambda: desk.answer(replace(q, role=(role + 1) % 3)))
    return 6


def all_states():
    counts = {}
    for arm in w.r.ARMS:
        case, menu, state, truth, rubric, sources = w.r.load(arm)
        candidates = w.r.direct(arm)
        verified = 0
        for state in product((-1, 0, 1), repeat=3):
            substituted = [row for row in sources if row["id"] != "delivered"]
            substituted += [{"id": "delivered", "text": w.r.w.renderer.public_conditions(case, state)}]
            with patch.object(w.r, "load", return_value=(case, menu, state, truth, rubric, substituted)):
                _, benchmark_record, expected_fields = w.r.compose(arm, candidates)
            actual, fields = w.finalize(arm, case, menu, state, candidates)
            assert actual == benchmark_record["text"] and fields == expected_fields
            assert len(actual.split()) <= (225 if arm == "mali" else 150)
            verified += 1
        counts[arm] = verified
    return counts


def run():
    results = replay_witnesses()
    optional = w.run("mali", (0, 1, 1), w.PROFILES["access-weak"], 2, "former", "archive")
    control = w.run("mali", (0, 1, 1), w.PROFILES["access-weak"], 2, "former-always", "archive")
    assert optional["decision"] == control["decision"] == "UNRESOLVED"
    assert optional["accounting"]["attempts"] + 1 == control["accounting"]["attempts"]
    assert w.g.options(w.r.load("mali")[1], optional["state"]) == w.g.options(
        w.r.load("mali")[1], control["state"])
    assert len(optional["public_trace"]) == 2
    case, *_ = w.r.load("cyprus")
    requests = []
    def adapter(req):
        requests.append(req)
        return w.fixture(case)(req)

    callback = w.run("cyprus", (0, 0, 1), w.PROFILES["even"], 2, "auto", adapter)
    assert callback["adapter"] == "callback" and callback["decision"] == "IMPASSE"
    assert [json.loads(req["messages"][-1]["content"])["role"] for req in requests] == [
        "Access desk", "Documentation desk"]
    malformed = w.run("cyprus", (0, 0, 1), w.PROFILES["even"], 2, "auto", lambda _: {})
    assert malformed["decision"] == "UNRESOLVED" and malformed["accounting"]["statuses"][0] == "rejected"

    def timed_out(_):
        raise TimeoutError

    timeout = w.run("cyprus", (0, 0, 1), w.PROFILES["even"], 2, "auto", timed_out)
    assert timeout["decision"] == "UNRESOLVED" and timeout["accounting"]["statuses"][0] == "timed_out"
    return {"delegate_callback_calls": len(requests), "callback_faults": ["empty_response", "timeout"], "archived": results, "archived_optional": {"reply_counts": [1, 2], "decision": "UNRESOLVED"},
            "invalid_receipts_rejected": invalid_receipts(),
            "role_local_request_checks": {arm: no_secret_prompt(arm) for arm in ("mali", "cyprus")},
            "compiler_state_checks": all_states()}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
