"""Optimize two public receipt states together when single-state search stalls."""
from hashlib import sha256
from itertools import combinations, product
from pathlib import Path

import numpy as np

import policy_search as p

a, f, n, o, D, s, HERE = p.a, p.f, p.n, p.o, p.D, p.s, p.HERE
TOL = p.TOL


def improve(points, mass, prior, opening):
    initial, start = p.improve(points, mass, prior, opening)
    cache = {tuple(initial[0]): (initial, start["final"])}
    states = tuple(int(i) for i in np.flatnonzero(mass.sum((0, 1)) > TOL))

    def team(chair):
        key = tuple(chair)
        if key not in cache:
            team_policy = chair, o.choose_response(chair, mass, points)
            cache[key] = (team_policy, o.measure(points, mass, prior, opening, team_policy))
        return cache[key]

    current = cache[tuple(initial[0])]
    trace = []
    priority = [2, 1]
    while True:
        size = priority.pop(0)
        chair, reward = current[0][0], current[1]["net"]
        candidates = []
        for mask in combinations(states, size):
            legal = [[int(i) for i in np.flatnonzero(D.CHAIR_LEGAL[state]) if i != chair[state]] for state in mask]
            for target in product(*legal):
                proposed = chair.copy()
                proposed[list(mask)] = target
                team_policy, performance = team(proposed)
                if performance["net"] > reward + TOL:
                    candidates.append((performance["net"], mask, target, team_policy, performance))
        if candidates:
            net, mask, target, action, result = max(candidates, key=lambda r: (
                r[0], tuple(-i for i in r[1]), tuple(-i for i in r[2])))
            current = action, result
            trace.append({"states": mask, "targets": target, "forecast_net": net})
            priority = [1, 2]
        elif not priority:
            break
    return current[0], {"one_state_updates": start["updates"], "additional_updates": trace,
                        "initial_search_tables": start["evaluated"], "additional_tables": len(cache) - 1,
                        "forecast_net": current[1]["net"]}


def summarize(rows):
    groups = {"all": rows}
    for row in rows:
        context = f"{row['suite']}/{row['prior_information']}"
        groups.setdefault(context, []).append(row)
        groups.setdefault(f"{context}/{row['review_offset']}", []).append(row)
    report = {}
    for name, group in groups.items():
        metrics = {"conditions": len(group)}
        for policy in ("single", "coordinated", "exact"):
            values = [row["routes"][policy] for row in group]
            margin = [item["net_over_fixed"] for item in values]
            metrics[policy] = {"wins": sum(v > TOL for v in margin), "losses": sum(v < -TOL for v in margin),
                               "mean_margin": sum(margin) / len(values), "worst_margin": min(margin),
                               "below_silence": sum(v["quality_over_silence"] < -TOL for v in values),
                               "mean_query_rate": sum(v["query_rate"] for v in values) / len(values)}
        report[name] = metrics
    return report


def run():
    path = HERE.parent / "information.json"
    original = n.read(o.replan.study.OLD)["training"]["budget_fit"]
    output = []
    for row in n.read(path)["runs"]:
        bank = np.array(row["bank"])
        actual, proxy = a.laws()[row["prior"]]
        prior = actual if row["prior_information"] == "correct_mixture" else proxy
        opening = o.replan.study.opening(f.views(bank)["4"], prior, original)
        mass, held = o.opening(*opening, prior), o.opening(*opening, actual)
        control = o.controls(bank, held, actual, opening)
        fixed = max(x["net"] for k, x in control.items() if k != "exact_ask_reply")
        for delta in (-7, 0, 7):
            review = bank.copy()
            review[3] = np.clip(review[3] + delta, 0, 70)
            forecast = f.views(review)["7"]
            single, _ = p.improve(forecast, mass, prior, opening)
            settings, trace = improve(forecast, mass, prior, opening)
            exact = o.exact_parts(mass, forecast)["exact_ask_reply"]
            ceiling = o.measure(forecast, mass, prior, opening, exact)["net"]
            routes = {}
            for k, action in (("single", single), ("coordinated", settings), ("exact", exact)):
                measured = o.measure(bank, held, actual, opening, action)
                nominal = o.measure(forecast, mass, prior, opening, action)
                assert measured["net"] <= control["exact_ask_reply"]["net"] + TOL
                routes[k] = {"net_over_fixed": measured["net"] - fixed, "query_rate": measured["queries"],
                             "quality_over_silence": measured["released"] - control["exact_no_request"]["released"],
                             "forecast_gap": ceiling - nominal["net"]}
            assert routes["coordinated"]["forecast_gap"] <= routes["single"]["forecast_gap"] + TOL
            output.append({k: row[k] for k in ("suite", "case", "prior", "prior_information")} |
                          {"review_offset": delta, "routes": routes, "search": trace})
    assert len(output) == 360
    pins = (Path(__file__), HERE / "block-protocol.md", path, Path(p.__file__))
    return {"rows": output, "summary": summarize(output),
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in pins}}


if __name__ == "__main__":
    s.q.e.emit(run())
