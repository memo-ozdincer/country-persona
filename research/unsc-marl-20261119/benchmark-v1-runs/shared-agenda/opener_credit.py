"""Fit an opening value function using exact downstream team credit."""
import json
from statistics import mean

import numpy as np

import experiment as e
import proof_feedback as p

FEES = (.015, .06, .15, .25)
MARGIN = 1e-10


def follower(scene, fee):
    links, prizes = scene["links"], scene["prizes"]
    return e.picks(
        tuple(tuple(r if r in (1, 2) and r in menu and links[1, r-1] * prizes[r-1] > fee else 0
                    for r in range(5)) for menu in e.MENUS)
    )


def features(scene, fee, second):
    priors, links, prizes = (scene[k] for k in ("p", "links", "prizes"))
    local = np.zeros((4, 3, 4))
    for i, menu in enumerate(e.MENUS):
        for action in menu[1:]:
            docket = action-1
            # Conditional partner availability before either desk receives a report.
            conditional = priors[i] / priors[i].sum()
            reply = float(conditional @ second[:, action, action])
            reached = links[0, docket]
            followup = reached * (1-e.FIRST_ONLY) * reply
            local[i, action] = (reached * e.FIRST_ONLY * prizes[docket],
                                followup * links[1, docket] * prizes[docket], fee, fee * followup)
    previous = p.stage(scene)[0][0, :, 0]
    return previous, local


def exact_targets(scene, fee, second):
    """Independent expected return conditional on the first desk's inventory."""
    _, _, wire, pay, _ = p.stage(scene)
    sent_first = (np.arange(3)[:, None, None] > 0).astype(float)
    sent_second = np.arange(3)[None, None, :] > 0
    value = pay - fee * (sent_first + sent_second)
    result = np.einsum("ij,ar,jrb,arb->ia", scene["p"], wire, second, value)
    return result / scene["p"].sum(axis=1, keepdims=True)


def fit(scenes):
    observed = []
    for scene in scenes:
        second = follower(scene, e.COST)
        previous, accounting = features(scene, e.COST, second)
        targets = exact_targets(scene, e.COST, second)
        for i, menu in enumerate(e.MENUS):
            for action in menu:
                observed.append((previous[i, action], accounting[i, action],
                                 targets[i, action], scene["p"][i].sum()))
    previous, accounting, target, weight = map(np.asarray, zip(*observed, strict=True))
    scale = np.sqrt(weight)
    reports = {}
    weights = {}
    for name, design in (("old-feature-fit", previous), ("accounting-fit", accounting)):
        coef, _, rank, _ = np.linalg.lstsq(design * scale[:, None], target * scale, rcond=None)
        delta = design @ coef - target
        reports[name] = dict(rank=int(rank), coef=coef.tolist(),
                             weighted_rmse=float(np.sqrt(np.average(delta**2, weights=weight))))
        weights[name] = coef
    return weights, reports


def best(values):
    return tuple(max(menu, key=lambda a: (values[i, a], -a)) for i, menu in enumerate(e.MENUS))


def settled(scene, fee, table, second):
    actual = p.outcomes(scene, e.picks(table), second)
    actual["net"] = actual["weighted_decisions"] - fee * actual["sends"]
    return actual


def evaluate(scene, fee, weight, original):
    second = follower(scene, fee)
    previous, accounting = features(scene, fee, second)
    y = exact_targets(scene, fee, second)
    feasible = np.asarray([(i, a) for i, menu in enumerate(e.MENUS) for a in menu]).T
    learning = accounting @ weight["accounting-fit"]
    delta = np.abs((learning-y)[tuple(feasible)])
    simple = accounting @ np.array([1., 1., -1., 0.])
    policies = {"original": tuple(original),
                "old-feature-fit": best(previous @ weight["old-feature-fit"]),
                "accounting-fit": best(learning),
                "ignore-follow-up-fee": best(simple),
                "exact": best(y)}
    scores = {name: settled(scene, fee, table, second) for name, table in policies.items()}
    for name, table in policies.items():
        analytical = sum(scene["p"][i].sum() * y[i, a] for i, a in enumerate(table))
        assert abs(analytical - scores[name]["net"]) < MARGIN
        assert scores[name]["net"] <= scores["exact"]["net"] + MARGIN
    return dict(regime=scene["mode"], payoff_abs_error=float(delta.max()), scores=scores, tables=policies)


def run():
    prior = e.HERE / "proof-feedback.json"
    old = json.loads(prior.read_text())
    weight, fit_report = fit(e.settings(False))
    held = e.settings(True)
    views = {}
    for fee in FEES:
        rows = [evaluate(scene, fee, weight, row["first"]) for scene, row in zip(held, old["held"], strict=True)]
        if fee == e.COST:
            for result, earlier in zip(rows, old["held"], strict=True):
                assert abs(result["scores"]["original"]["net"] - earlier["scores"]["fixed-follow-on"]["net"]) < MARGIN
                assert abs(result["scores"]["exact"]["net"] - earlier["scores"]["fixed"]["net"]) < MARGIN
        metrics = {}
        for arm in rows[0]["scores"]:
            m = {measure: mean(r["scores"][arm][measure] for r in rows) for measure in rows[0]["scores"][arm]}
            m["scenarios_below_exact"] = int(sum(r["scores"]["exact"]["net"] - r["scores"][arm]["net"] > MARGIN
                                                for r in rows))
            metrics[arm] = m
        views[fee] = dict(metrics=metrics, maximum_value_error=max(r["payoff_abs_error"] for r in rows), held=rows)
    return dict(protocol=e.digest(e.HERE / "opener-credit-protocol.md"), prior=e.digest(prior),
                fit=fit_report, evaluation=views)


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
