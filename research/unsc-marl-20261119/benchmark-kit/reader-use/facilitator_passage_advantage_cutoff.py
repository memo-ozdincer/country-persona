"""Calibrate when to ask on development cases with the fitted value model."""
import json

import numpy as np

import facilitator_passage_advantage_fit as study

EPSILON = 1e-10


def scores(development, team, weights):
    result = []
    for public, target in development.values():
        for label in study.fit.live.PRIORS:
            prior = study.R.TEST_PRIORS[label]
            _, mass, features, (_, replies) = study.context(public, prior, team)
            advantage, visit = study.advantages(target, mass, replies, study.fit.PERFECT)
            prediction = features @ weights
            best = np.where(study.QUESTIONS, prediction, -np.inf).argmax(-1)
            strongest = prediction[np.arange(8), best]
            strongest[~study.QUESTIONS.any(-1) | (visit <= 1e-12)] = 0
            result.append((strongest, visit * advantage[np.arange(8), best], visit))
    return np.stack(result)


def score(rows, cutoff):
    estimates, gains, visit = rows.transpose(1, 0, 2)
    asks = estimates > cutoff + EPSILON
    return {"gain_over_silence": float((asks * gains).sum(-1).mean()),
            "requests": float((asks * visit).sum(-1).mean())}


def choose(rows):
    estimates = rows[:, 0]
    options = np.unique(np.r_[0., estimates[estimates > 0.]])
    evaluated = [(float(cutoff), score(rows, cutoff)) for cutoff in options]
    cutoff, best = max(evaluated, key=lambda item: (round(item[1]["gain_over_silence"], 10), item[0]))
    return {"cutoff": cutoff, "calibrated": best, "zero_cutoff": score(rows, 0.), "options": len(options)}


def run():
    read, joint = study.joint.historic.read, study.joint
    archive = read(study.EVIDENCE / "results.json")
    team = read(study.adaptive.EVIDENCE / "results.json")["fit"]
    development = study.fit.OLD.base.cases()[0]
    weights = np.asarray(archive["coefficients"])
    assert np.allclose(weights, study.fit_values(development, team)[0], rtol=0, atol=1e-12)
    fit = choose(scores(development, team, weights))
    groups = {name: name.split("/", 1)[0] for name in development}
    folds = {}
    for omitted in sorted(set(groups.values())):
        train = {name: row for name, row in development.items() if groups[name] != omitted}
        test = {name: row for name, row in development.items() if groups[name] == omitted}
        fold_weights, _ = study.fit_values(train, team)
        cutoff = choose(scores(train, team, fold_weights))["cutoff"]
        test_scores = scores(test, team, fold_weights)
        folds[omitted] = {"train_cutoff": cutoff, "held": list(test), "zero": score(test_scores, 0.),
                          "calibrated": score(test_scores, cutoff)}
    held = {}
    for docket, (points, channel) in joint.held().items():
        held[docket] = {}
        for label, openings in archive["cases"][docket].items():
            prior = study.R.TEST_PRIORS[label]
            adaptive_row = read(study.adaptive.EVIDENCE / "results.json")["cases"][docket][label]
            held[docket][label] = {}
            for opening_name, arm in (("fitted_opening", "adaptive"), ("planner_opening", "declared_block_planner")):
                opening = tuple(np.asarray(x) for x in adaptive_row[arm]["team"][:2])
                _, mass, features, (_, replies) = study.context(points, prior, team, opening)
                prediction = features @ weights
                prediction[:, 1:] -= fit["cutoff"]
                prediction[mass.sum((0, 1)) <= 1e-12] = 0.
                chair = study.best_question(prediction)
                current = joint.metric((*opening, chair, replies), prior, points, channel)
                original = openings[opening_name]["policies"]["regressed_advantage"]["net"]
                silence = openings[opening_name]["policies"]["fixed_team_silence"]["net"]
                best = openings[opening_name]["policies"]["measured_counterfactual"]["net"]
                assert silence <= best + 1e-10 and current["net"] <= best + 1e-10
                held[docket][label][opening_name] = {
                    "questions": chair.tolist(), "net": current["net"], "requests": current["expected_requests"],
                    "gain_over_zero_cutoff": current["net"] - original, "gain_over_fixed_team_silence": current["net"] - silence,
                }
    return {"cutoff_fit": fit, "development_folds": folds, "held": held}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
