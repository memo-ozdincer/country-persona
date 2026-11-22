"""Replay verified source pointers through learned and optimized routing policies."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import numpy as np

import unifil_final_review as primary
import unifil_span_transport as transport
import unifil_verified_transport as renderer

study, judge, route = primary.study, primary.judge, primary.routing


def compile_one(mask, role_notes, comparison_accepted):
    received = [role for i, role in enumerate(study.FIELDS) if mask & (1 << i)]
    present = [role for role in received if role in role_notes]
    parts = [renderer.TEXT[role] for role in present]
    units = dict(primary.PUBLIC)
    for role in present:
        index = study.FIELDS.index(role)
        units[5 + index] = ["M", [5 + present.index(role)], [3 + index]]
    if comparison_accepted and {"brazil", "china"} <= set(present):
        parts.append(renderer.COMPARISON)
        start = 5 + len(present)
        units[8] = ["M", [start], [3, 4]]
        units[9] = ["M", [5, 6, start + 1], [3, 4]]
    body = "\n\n".join(parts)
    text = "\n\n".join(filter(None, [study.PUBLIC, body]))
    verdict = {"units": [units.get(i, ["U", [], []]) for i in range(10)], "guard": ["C", [], []]}
    with patch.object(judge.study, "packet", study.packet):
        scoring = judge.interpret(str(mask), text, verdict)
    assert len(body.split()) <= study.BODY_WORDS
    return {"received": received, "selected_exact_spans": {role: role_notes[role] for role in present},
            "comparison_accepted": 8 in units, "points": scoring["score"]["final"]["lower"],
            "body_words": len(body.split()), "text": text, "assessment": scoring}


def summarize(directory, exact):
    decisions, relations, notes = transport.replay(directory)
    fitted = json.loads(transport.FIT.read_text())
    assert study.common.runner.digest(study.OUT / "verified-transport.json") == fitted["evaluation"]["verified"]["sha256"]
    learned = study.common.as_policy(fitted["policy"])
    original = json.loads(study.FROZEN.read_text())
    outside = study.common.as_policy(original["policies"]["interactive"])
    regimes = {}
    for order in ("forward", "reverse", "stable"):
        tests = tuple(transport.ORDERS) if order == "stable" else (order,)
        accepted = {role: notes[role, tests[0]] for role in study.FIELDS
                    if all((role, t) in notes for t in tests)}
        assert all(notes[role, t] == text for role, text in accepted.items() for t in tests)
        relation = all(relations[f"comparison.intact.{t}"]["accepted"] for t in tests)
        regimes[order] = (accepted, relation)
    # Withhold the Brazil field when the named source lacks the required qualifier.
    # The model's recorded decisions, including responses to the distractor, are kept above.
    stable = regimes["stable"][0]
    regimes["missing_brazil"] = ({role: text for role, text in stable.items() if role != "brazil"}, False)
    bound_cache = {}
    result = {}
    for condition, (role_notes, bridge) in regimes.items():
        bank = [compile_one(int(mask), role_notes, bridge) for mask in route.STATES]
        values = np.array([cell["points"] for cell in bank])
        matrix = route.receipt_matrix(values, route.TRAIN_LOSS)
        priors = {}
        for name, prior in route.TEST_PRIORS.items():
            def evaluate(policy, erased=False):
                return route.evaluate(policy, prior, values, route.TRAIN_LOSS, force_missing=erased)

            arms = {
                "rubric_fit": evaluate(learned),
                "request_erased": evaluate(learned, erased=True),
                "frozen_outer_space": evaluate(outside),
                "exact_independent": evaluate(route.best_silent(prior, matrix)),
            }
            if exact:
                key = (tuple(values), name)
                if key not in bound_cache:
                    bound, count = route.exact_optional(prior, matrix, route.TRAIN_LOSS)
                    bound_cache[key] = {**evaluate(bound), "request_maps_examined": count}
                upper = bound_cache[key]
                assert upper["net"] + 1e-9 >= max(a["net"] for a in arms.values())
                arms["exact_optional"] = upper
            priors[name] = arms
        result[condition] = {"bank": bank, "receipt_values": values.tolist(), "priors": priors}
    return {
        "scope": "Observed model selections from bounded, authored menus. Exact source checks and deterministic "
                 "rendering. Field-level link loss replay only. Freeze the input policy and mappings.",
        "transcript_sha256": study.common.runner.digest(directory / "transcript.jsonl"),
        "policy_sha256": study.common.runner.digest(transport.FIT),
        "source_decisions": decisions, "comparison_decisions": relations,
        "counterfactuals": result,
    }


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--directory", type=Path, default=transport.OUT)
    cli.add_argument("--exact", action="store_true")
    args = cli.parse_args()
    print(json.dumps(summarize(args.directory, args.exact), indent=2, ensure_ascii=False))
