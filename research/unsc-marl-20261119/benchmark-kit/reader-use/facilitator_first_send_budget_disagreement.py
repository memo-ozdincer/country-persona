"""Isolate budget and admission assumptions behind the Resolution 2719 loss."""
import json

import numpy as np

import facilitator_first_send_fit as run_fit

study, fit, joint = run_fit.study, run_fit.fit, run_fit.joint


def run():
    base = study.budget.read(study.OLD)
    old = study.budget.read(study.EVIDENCE / "results.json")
    prior_fit = study.budget.read(run_fit.EVIDENCE / "results.json")
    _, channel = joint.held()["2719"]
    bank = base["cases"]["2719"]["outcomes"]["70"]
    public, target = map(np.asarray, (bank["public_scores"], bank["terminal_scores"]))
    results = {}
    for law, archived in old["cases"]["2719"]["70"].items():
        prior = study.R.TEST_PRIORS[law]
        left, right, question, reply = (np.asarray(archived["response_aware"]["policy"][role])
                                         for role in ("left", "right", "request", "response"))
        mass = joint.opening(left, right, prior)
        visit = np.einsum("rbm,m->rb", mass, fit.heard(study.D.one_hot(question))[:, 0])
        teams = {"response_aware": (left, right, question, reply)}
        for costs, scores in (("whole_notes", public), ("reviewed_prefixes", target)):
            for admission, estimate in (("ideal_admission", fit.PERFECT), ("measured_admission", channel)):
                rewards = run_fit.counterfactuals(mass, question, fit.value(scores, estimate))
                best = np.where(run_fit.LEGAL, rewards, -np.inf).argmax(-1)
                best = np.where(np.ptp(rewards, axis=-1) == 0, reply[:, :, 0], best)
                teams[f"{costs}/{admission}"] = (left, right, question, run_fit.replace(reply, best))
        rows = run_fit.record(teams, lambda t: joint.metric(t, prior, target, channel),
                              archived, mass, fit.value(target, channel))
        reference = prior_fit["cases"]["2719"]["70"][law]
        assert rows["whole_notes/ideal_admission"]["net"] == reference["declared_first_send"]["net"]
        assert rows["reviewed_prefixes/measured_admission"]["net"] == reference["hindsight_first_send"]["net"]
        results[law] = {"outcomes": rows, "no_question_state_mass": visit.tolist()}
    return {"declared_scores": public.tolist(), "reviewed_prefix_scores": target.tolist(), "laws": results}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
