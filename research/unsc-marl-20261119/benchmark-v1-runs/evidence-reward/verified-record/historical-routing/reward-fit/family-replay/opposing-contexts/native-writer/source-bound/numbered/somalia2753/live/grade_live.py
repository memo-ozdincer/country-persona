"""Score every unedited dispatcher record against the frozen source rubric."""
from hashlib import sha256
from pathlib import Path

import live_somalia as w

n, e, q = w.n, w.e, w.q
HERE = Path(__file__).resolve().parent


def run():
    case = n.read(w.t.SOURCE)
    stored = n.read(w.OUT / "dispatch.json")
    sources = {r["id"]: r["text"] for r in case["public"]}
    reviewed = {}
    for arm, trace in stored["arms"].items():
        output = trace["record"]
        used = {role: set(ids) for role, ids in output["used"].items()}
        views = {role for role, bit in zip(case["roles"], w.BITS[1:]) if trace["receipt"] & bit}
        assert all(not ids or role in views for role, ids in used.items())
        calls = [{}, {}, {"text": output["text"], "termination": "complete"}]
        packet = e.final_packet(case, calls)

        def criterion(key, source, span, eligible):
            return {"id": key, "status": "met" if eligible else "unmet",
                    "source": [{"block": x, "quote": sources[x]} for x in source] if eligible else [],
                    "response": span if eligible else "",
                    "reason": "Source-bound clause meets the stated requirement." if eligible else
                              "At least one required source-bound clause is absent."}

        marks = [criterion(k, (source,), case["public_text"], True) for k, source in q.PUBLIC.items()]
        marks.extend(criterion(f"{role}-position", (role,), output["local"].get(role, ""), expected <= used[role])
                     for role, expected in q.COMPLETE.items())
        for claim, (required, _) in q.INTERACTIONS.items():
            eligible = claim in output["comparison"]
            assert eligible == all(expected <= used[role] for role, expected in required.items())
            marks.append(criterion(claim, tuple(required), output["text"], eligible))
        verdict = {"id": packet["id"], "units": marks,
                   "guard": {"status": "clear", "response": "", "source": [],
                             "reason": "Mandate and speaker claims are formed from the admitted source spans."}}
        score = e.final_score(case, calls, verdict)
        reviewed[arm] = {"asked": trace["query"], "heard": trace["heard"], "sent": trace["reply"],
                         "receipt": trace["receipt"], "cost": trace["cost"],
                         "net": score["released_70"] - trace["cost"], "score": score,
                         "packet": packet, "marks": verdict}
    pins = (Path(__file__), w.OUT / "dispatch.json", w.t.SOURCE, HERE / "plan.json", Path(q.__file__))
    return {"records": reviewed, "physical_calls": stored["physical_calls"],
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in pins}}


if __name__ == "__main__":
    e.emit(run())
