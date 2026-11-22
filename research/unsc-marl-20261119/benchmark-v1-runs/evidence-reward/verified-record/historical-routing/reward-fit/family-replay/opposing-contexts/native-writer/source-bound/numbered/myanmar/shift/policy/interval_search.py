"""Qualify coordinated routing and same-information fixed controls under grading error."""
from hashlib import sha256
from pathlib import Path

import numpy as np

import block_search as b

p, f, n, a, o, D, s, HERE = b.p, b.f, b.n, b.a, b.o, b.D, b.s, b.HERE
TOL = p.TOL


def forecasts(calibration, grade):
    measured = dict(calibration)
    measured[3] = grade
    base = measured[0]
    singletons = sum(measured[key] for key in (1, 2, 4)) - 2 * base
    pairs = ((3, 1, 2), (5, 1, 4), (6, 2, 4))
    interaction = sum(measured[key] - measured[i] - measured[j] + base for key, i, j in pairs)
    assert set(measured) == set(range(7))
    return np.array([measured[k] for k in range(7)] + [float(np.clip(singletons + interaction, 0, 70))])


def select(catalog, values, filtered):
    table = {k: row for k, row in values.items() if (not filtered or k[1] != "coordinated")}
    eligible = [k for k, performance in table.items() if performance[0] >= -TOL]
    if eligible:
        chosen = max(eligible, key=lambda k: (table[k][1], table[k][2], -abs(k[0] - 1)))
    else:
        chosen = max(table, key=lambda k: (*table[k], -abs(k[0] - 1)))
    return chosen, catalog[chosen]


def evaluate_locked(calibration, grade, prior, opening, mass, cache):
    grades = [float(np.clip(grade + offset, 0, 70)) for offset in (-7, 0, 7)]
    predictions = [forecasts(calibration, value) for value in grades]

    def policies(grade, prediction):
        if grade not in cache:
            chair = {f"fixed_{target}": np.where(D.CHAIR_LEGAL[:, target], target, 0) for target in range(4)}
            local = {k: (q, o.choose_response(q, mass, prediction)) for k, q in chair.items()}
            local["coordinated"], _ = b.improve(prediction, mass, prior, opening)
            cache[grade] = local
        return cache[grade]

    menus = [policies(grade, prediction) for grade, prediction in zip(grades, predictions, strict=True)]
    catalog = {(index, label): decision for index, menu in enumerate(menus) for label, decision in menu.items()}

    def measure(policy, points):
        return o.measure(points, mass, prior, opening, policy)

    comparators = []
    for index, prediction in enumerate(predictions):
        fixed = {name: measure(policy, prediction) for name, policy in menus[index].items()
                 if name != "coordinated"}
        comparators.append((fixed["fixed_0"]["released"], max(row["net"] for row in fixed.values())))
    values = {}
    for key, policy in catalog.items():
        evaluated = [measure(policy, forecast) for forecast in predictions]
        releases = min(row["released"] - quiet for row, (quiet, _) in zip(evaluated, comparators))
        margin = min(row["net"] - fixed for row, (_, fixed) in zip(evaluated, comparators))
        values[key] = (releases, margin, evaluated[1]["net"])
    nominal = (1, "coordinated")
    return {"nominal": (nominal, catalog[nominal]),
            "interval_fixed": select(catalog, values, filtered=True),
            "interval_team": select(catalog, values, filtered=False)}


def summarize(rows):
    groups = {"all": rows}
    for row in rows:
        context = f"{row['suite']}/{row['prior_information']}"
        groups.setdefault(context, []).append(row)
        groups.setdefault(f"{context}/{row['review_offset']}", []).append(row)
    dump = {}
    for key, group in groups.items():
        methods = {}
        for mode in ("nominal", "interval_fixed", "interval_team"):
            stats = [row["routes"][mode] for row in group]
            net = [value["net_over_oracle_fixed"] for value in stats]
            pair_gain = [r["routes"][mode]["net_over_oracle_fixed"] - r["routes"]["interval_fixed"]["net_over_oracle_fixed"]
                         for r in group]
            methods[mode] = {"wins_vs_oracle": sum(x > TOL for x in net), "losses_vs_oracle": sum(x < -TOL for x in net),
                             "mean_margin_vs_oracle": sum(net) / len(net),
                             "wins_vs_interval_fixed": sum(x > TOL for x in pair_gain),
                             "losses_vs_interval_fixed": sum(x < -TOL for x in pair_gain),
                             "mean_margin_vs_interval_fixed": sum(pair_gain) / len(pair_gain),
                             "below_silence": sum(v["quality_over_silence"] < -TOL for v in stats),
                             "adaptive_choices": sum(v["selected"][1] == "coordinated" for v in stats)}
        dump[key] = {"rows": len(group), "methods": methods}
    return dump


def run():
    path = HERE.parent / "information.json"
    block = HERE / "block-results.json"
    raw = {(r["suite"], r["case"], r["prior_information"], r["prior"], r["review_offset"]): r
           for r in n.read(block)["rows"]}
    initializer = n.read(o.replan.study.OLD)["training"]["budget_fit"]
    laws = a.laws()
    result = []
    for case in n.read(path)["runs"]:
        bank = np.array(case["bank"])
        calibration = {i: bank[i] for i in range(7) if i != 3}
        actual, proxy = laws[case["prior"]]
        prior = actual if case["prior_information"] == "correct_mixture" else proxy
        opening = o.replan.study.opening(f.views(bank)["4"], prior, initializer)
        mass, held = o.opening(*opening, prior), o.opening(*opening, actual)
        oracle = o.controls(bank, held, actual, opening)
        best = max(v["net"] for k, v in oracle.items() if k != "exact_ask_reply")
        quiet = oracle["exact_no_request"]["released"]
        cache = {}
        for offset in (-7, 0, 7):
            grade = float(np.clip(bank[3] + offset, 0, 70))
            decisions = evaluate_locked(calibration, grade, prior, opening, mass, cache)
            values = {}
            for method, (key, policy) in decisions.items():
                value = o.measure(bank, held, actual, opening, policy)
                values[method] = {"selected": (key[0] - 1, key[1]), "net_over_oracle_fixed": value["net"] - best,
                                  "quality_over_silence": value["released"] - quiet}
            lookup = (case["suite"], case["case"], case["prior_information"], case["prior"], offset)
            assert abs(values["nominal"]["net_over_oracle_fixed"] - raw[lookup]["routes"]["coordinated"]["net_over_fixed"]) <= TOL
            result.append({k: case[k] for k in ("suite", "case", "prior_information", "prior")} |
                          {"review_offset": offset, "routes": values})
    pins = (Path(__file__), HERE / "uncertainty-protocol.md", path, block, Path(b.__file__))
    return {"rows": result, "summary": summarize(result),
            "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in pins}}


if __name__ == "__main__":
    s.q.e.emit(run())
