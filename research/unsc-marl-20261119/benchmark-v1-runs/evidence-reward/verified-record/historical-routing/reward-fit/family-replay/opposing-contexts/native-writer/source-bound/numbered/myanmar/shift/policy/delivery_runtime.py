"""Dispatch the actual decentralized actions and replay the source-bound final records."""
from hashlib import sha256
from itertools import product
from pathlib import Path

import numpy as np

import interval_search as c

n, o, D, s, a, f, HERE = c.n, c.o, c.D, c.s, c.a, c.f, c.HERE
BITS = (0, 1, 2, 4)


def episode(holder, openings, team, delivered):
    left, right = holder
    op1, op2, query_ok, reply_ok = delivered
    first = int(openings[0][left])
    second = int(openings[1][right])
    assert BITS[first] & ~left == BITS[second] & ~right == 0
    live = BITS[first] * op1 | BITS[second] * op2
    asks, replies = team
    query = int(asks[live])
    assert D.CHAIR_LEGAL[live, query]
    heard = query * query_ok
    reply = int(replies[right, second, heard])
    legal_replies = np.broadcast_to(D.FINAL_LEGAL, (*replies.shape, 4))
    assert BITS[reply] & ~right == 0 and legal_replies[right, second, heard, reply]
    end = live | BITS[reply] * reply_ok
    cost = float(D.SEND_COST[first] + D.SEND_COST[second] + D.QUERY_COST[query] + D.SEND_COST[reply])
    return {"opener_actions": (first, second), "public_opening": live, "query": query,
            "responder_view": (right, second, heard), "reply": reply, "receipt": end, "cost": cost}


def trace_table(law, opening, policies, bank):
    totals = {mode: np.zeros(11) for mode in policies}
    witness = None
    for left, right in product(range(8), repeat=2):
        for bits in product((0, 1), repeat=4):
            weight = law[left, right] * (1 - D.LOSS) ** sum(bits) * D.LOSS ** (4 - sum(bits))
            if weight == 0:
                continue
            routes = {}
            for mode, policy in policies.items():
                outcome = episode((left, right), opening, policy, bits)
                receipt = outcome["receipt"]
                totals[mode][receipt] += weight
                totals[mode][8] += outcome["cost"] * weight
                totals[mode][9] += bool(outcome["query"]) * weight
                totals[mode][10] += bank[receipt] * weight
                routes[mode] = outcome | {"released": bank[receipt]}
            if witness is None and routes["interval_team"]["released"] > routes["interval_fixed"]["released"]:
                witness = {"world": (left, right), "delivery": bits, "routes": routes, "probability": float(weight)}
    return {mode: {"receipt_mass": val[:8].tolist(), "cost": float(val[8]), "queries": float(val[9]),
                   "released": float(val[10]), "net": float(val[10] - val[8])}
            for mode, val in totals.items()}, witness


def composers():
    import compact_packer as un
    import cover_pack as my

    folder = s.t.HERE.parent
    unifil = n.read(folder / "packed-grades.json")
    selection = {role: result[0] for role, result in unifil["selection"].items()}
    deck = un.w.plan()
    public = unifil["rendered"]["native"]["0"]["text"]
    myanmar = n.read(s.t.HERE / "intact-grades.json")
    picked = {role: result[0] for role, result in myanmar["posthoc_format_normalization"].items()}
    my_deck = s.t.plan()
    checks = {
        "unifil": (unifil["assessed"]["native"], selection, lambda mask, local: un.pack(mask, local, deck, public)),
        "myanmar": (myanmar["records"]["rank_normalized"], picked,
                    lambda mask, local: my.preserve(mask, local, my_deck, preserve_intact=True)),
    }
    records = {}
    for name, (grades, selections, render) in checks.items():
        suite = {}
        for mask in range(8):
            local = {role: value if mask & bit else []
                     for bit, (role, value) in zip(BITS[1:], selections.items(), strict=True)}
            compiled = render(mask, local)
            for bit, value in zip(BITS[1:], compiled["used"].values(), strict=True):
                assert not value or mask & bit
            reviewed = grades[str(mask)]
            assert compiled["text"] == reviewed["packet"]["answer"]
            assert len(compiled["text"].split()) == reviewed["score"]["words"]
            suite[mask] = {"text": compiled["text"], "released": reviewed["score"]["released_70"]}
        records[name] = suite
    return records


def run():
    record_banks = composers()
    inputs = (s.t.HERE.parent / "packed-grades.json", s.t.HERE / "intact-grades.json")
    starter = n.read(o.replan.study.OLD)["training"]["budget_fit"]
    output = {}
    seen = {}
    for name, records in record_banks.items():
        bank = np.array([r["released"] for r in records.values()], dtype=float)
        calibration = {i: bank[i] for i in range(7) if i != 3}
        for label, (truth, proxy) in a.laws().items():
            for info, prior in (("correct_mixture", truth), ("dominant_only", proxy)):
                opening = o.replan.study.opening(f.views(bank)["4"], prior, starter)
                mass, held = o.opening(*opening, prior), o.opening(*opening, truth)
                result = c.evaluate_locked(calibration, bank[3], prior, opening, mass, {})
                policies = {mode: decision for mode, (_, decision) in result.items()}
                observed, witness = trace_table(truth, opening, policies, bank)
                for mode, policy in policies.items():
                    predicted = o.measure(bank, held, truth, opening, policy)
                    assert all(np.allclose(measured, predicted[key], atol=1e-10, rtol=0)
                               for key, measured in observed[mode].items())
                if witness and name not in seen:
                    for value in witness["routes"].values():
                        value["record"] = records[value["receipt"]]["text"]
                    seen[name] = {"prior": label, "information": info} | witness
                output[f"{name}/{label}/{info}"] = observed
    pins = (Path(__file__), HERE / "runtime-protocol.md", Path(c.__file__), *inputs)
    return {"recompiled_receipt_masks": len(record_banks) * 8, "conditions": output, "witnesses": seen,
            "sha256": {file.name: sha256(file.read_bytes()).hexdigest() for file in pins}}


if __name__ == "__main__":
    s.q.e.emit(run())
