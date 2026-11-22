"""Separate whole-note length assumptions from final-vote credit in planning."""
from itertools import product
import json

import numpy as np

import facilitator_budget_policy as study

fit, joint, R = study.fit, study.joint, study.R
verbatim = study.verbatim


def permissive_prefix_bank(limit):
    datasets, _ = verbatim.inputs()
    notes = datasets["change_wording/declared"]
    by_desk = {note["desk"]: note for note in notes}
    packet = study.read(verbatim.live.PACKET)
    ordered = [by_desk[card["speaker"]] for card in packet["cards"]]
    weights = {row["id"]: row["points"] for row in packet["criteria"]}
    labels = study.read(study.VERBATIM / "annotations.json")
    rules = study.read(study.VERBATIM / "grammar.json")["criteria"]
    # The historical authored bank grants AF with Procedure and France.
    # Here the alternative allows France's final vote to follow from
    # unanimous adoption when the note actually names its abstention.
    rules["AF"] = [atom for atom in rules["AF"] if atom != "fr_affirmative_final_explicit"]
    result = []
    for received in range(8):
        got = [n for i, n in enumerate(ordered) if received & (1 << i)]
        domains = [range(len(verbatim.SPLIT.split(n["text"])) + 1) for n in got]
        candidates = (verbatim.evaluate(got, counts, labels, rules, weights) for counts in product(*domains))
        result.append(42 + max(c["guarded_points"] for c in candidates if c["words"] <= limit))
    return np.asarray(result)


def run():
    existing = study.read(study.EVIDENCE / "results.json")
    full, admissions = joint.held()["2719"]
    pkt = study.read(verbatim.live.PACKET)
    vote = next(row for row in pkt["criteria"] if row["id"] == "AF")
    stricter = full - np.asarray([vote["points"] * (mask & vote["mask"] == vote["mask"]) for mask in range(8)])
    docket = existing["cases"]["2719"]
    rows = {}
    for limit_text, control in docket["outcomes"].items():
        limit = int(limit_text)
        actual = np.asarray(control["terminal_scores"])
        assert np.array_equal(actual, study.reviewed_prefix_bank(limit))
        beliefs = {"whole_inferred_vote": study.projection(full, docket["generic_note_words_with_labels"], limit),
                   "whole_explicit_vote": study.projection(stricter, docket["generic_note_words_with_labels"], limit),
                   "prefix_inferred_vote": permissive_prefix_bank(limit), "prefix_explicit_vote": actual}
        results = {}
        for label in fit.live.PRIORS:
            prior = R.TEST_PRIORS[label]
            quiet = control["priors"][label]["hindsight_no_request"]["net"]
            results[label] = {}
            for name, public in beliefs.items():
                opener = joint.exact_no_request(prior, public, fit.PERFECT)
                policy, _ = joint.block(opener, prior, public, fit.PERFECT)
                scored = joint.metric(policy, prior, actual, admissions)
                results[label][name] = {"advantage_over_exact_silence": scored["net"] - quiet,
                                        "requests": scored["expected_requests"],
                                        "first_actions": [np.asarray(x).tolist() for x in policy[:3]]}
            old = control["priors"][label]["declared_block"]["vs_hindsight_no_request"]
            assert abs(results[label]["whole_inferred_vote"]["advantage_over_exact_silence"] - old) < 1e-12
        rows[limit_text] = {"planner_score_assumptions": {k: v.tolist() for k, v in beliefs.items()},
                            "comparison": results}
    return {"cases": rows, "perfect_measured_admission": bool(np.array_equal(admissions, fit.PERFECT))}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
