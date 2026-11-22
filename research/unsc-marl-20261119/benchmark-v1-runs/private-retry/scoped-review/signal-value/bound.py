"""Enumerate the best dispatch policy over archived review observations."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
INPUT = HERE.parent / "indexed/compact.json"
RAW_CALLS = HERE.parent / "indexed/evidence/calls.jsonl"
ORDERS = ("forward", "reverse")
SINGLES = {0: 42, 1: 50, 2: 52, 4: 49}
CHANNELS = ("none", "owner", "pooled", "all")
FEES = (0., .15, .75)
LAWS = {"independent-40": (.4,), "independent-80": (.8,), "shared-40-or-80": (.4, .8)}


def estimate(data, raw, receipt, format_visible, arm, fee):
    legal = [m for m in range(8) if m & receipt == m]
    grades = []
    formats = []
    signals = []
    for order in ORDERS:
        outcomes = SINGLES.copy()
        flags = {}
        responses = {}
        for mask in legal:
            if mask in SINGLES:
                continue
            key = f"{order}/{mask}"
            row = data["archive"][key]
            outcomes[mask] = row["grade"]
            flags[mask] = row["format"]
            for name, reports in data["verdicts"].get(key, {}).items():
                if arm == "all" or (arm == "pooled" and name == "pooled") or (arm == "owner" and name != "pooled"):
                    for mapping, report in reports.items():
                        response = raw[f"{key}/{name}/{mapping}"]
                        assert response == report["response"].replace(" ", "")
                        responses[(mask, name, mapping)] = response
        grades.append(outcomes)
        formats.append(flags)
        signals.append(responses)

    public = [tuple(f.items()) if format_visible else () for f in formats]
    states = {view: tuple(i for i, value in enumerate(public) if value == view) for view in public}
    queries = sorted(set(signals[0]) | set(signals[1]))
    exact = mean(max(row[m] for m in legal) for row in grades)
    fallback = max(SINGLES[m] for m in legal if m in SINGLES)

    def score(group, action):
        return mean(grades[w][action] for w in group)

    def branch(group, query):
        observations = {}
        for world in group:
            signal = signals[world].get(query)
            observations.setdefault(signal, []).append(world)
        return observations

    def cost(group, query):
        return fee * mean(query in signals[w] for w in group)

    @lru_cache(None)
    def solve(group, available):
        action = max(legal, key=lambda m: (score(group, m), -m.bit_count(), -m))
        best = (score(group, action), {"publish": action})
        if len(group) == 1:
            return best
        for j, query in enumerate(available):
            children = branch(group, query)
            if len(children) == 1:
                continue
            remaining = available[:j] + available[j + 1:]
            net = -cost(group, query)
            then = []
            for observed, child in children.items():
                child_net, child_policy = solve(tuple(child), remaining)
                net += len(child) * child_net / len(group)
                then.append({"reply": observed, "action": child_policy})
            if net > best[0] + 1e-10:
                best = (net, {"ask": query, "then": then})
        return best

    def replay(world, policy):
        if "publish" in policy:
            return grades[world][policy["publish"]]
        query = policy["ask"]
        signal = signals[world].get(query)
        option, = (item for item in policy["then"] if item["reply"] == signal)
        return replay(world, option["action"]) - fee * (signal is not None)

    def independently_check(group, measured):
        no_query = max(score(group, action) for action in legal)
        separators = [q for q in queries if len(branch(group, q)) > 1]
        hindsight = mean(max(grades[w][m] for m in legal) for w in group)
        savings = min((cost(group, q) for q in separators), default=float("inf"))
        independent = max(no_query, hindsight - savings)
        assert abs(measured - independent) < 1e-10
        return no_query, separators

    cohorts = []
    for view, group in states.items():
        best, policy = solve(group, tuple(queries))
        start, separators = independently_check(group, best)
        assert abs(mean(replay(w, policy) for w in group) - best) < 1e-10
        cohorts.append({"orders": [ORDERS[w] for w in group], "visible_formats": view, "net": best,
                        "prior_only": start, "separating_queries": separators, "policy": policy})
    net = sum(len(c["orders"]) * c["net"] for c in cohorts) / len(ORDERS)
    prior_only = sum(len(c["orders"]) * c["prior_only"] for c in cohorts) / len(ORDERS)
    assert fallback <= prior_only + 1e-9 <= net + 1e-9 <= exact + 1e-9
    return {"net": net, "prior_only": prior_only, "exact": exact, "fallback": fallback, "cohorts": cohorts}


def run():
    data = json.loads(INPUT.read_text())
    raw = {row["id"]: row["response"]["text"] for row in map(json.loads, RAW_CALLS.read_text().splitlines())}
    assert len(raw) == 46
    for mask in (1, 2, 4):
        assert data["archive"][f"forward/{mask}"]["grade"] == SINGLES[mask]
    views = {}
    for name, visible in (("public_format", True), ("hidden_format", False)):
        policies = {}
        for arm in CHANNELS:
            policies[arm] = {}
            for fee in FEES:
                by_mask = {mask: estimate(data, raw, mask, visible, arm, fee) for mask in range(8)}
                summary = {}
                for law, rates in LAWS.items():
                    weights = {m: mean(p**m.bit_count() * (1-p)**(3-m.bit_count()) for p in rates)
                               for m in by_mask}
                    assert abs(sum(weights.values()) - 1.) < 1e-10
                    summary[law] = {k: sum(by_mask[m][k] * weights[m] for m in by_mask)
                                    for k in ("fallback", "prior_only", "net", "exact")}
                policies[arm][str(fee)] = {"summary": summary, "receipts": by_mask}
        views[name] = policies
    return {"input_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
            "raw_calls_sha256": hashlib.sha256(RAW_CALLS.read_bytes()).hexdigest(), "views": views}


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
