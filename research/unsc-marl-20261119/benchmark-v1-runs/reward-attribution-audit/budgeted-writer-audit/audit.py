"""Compare cross-docket admission and limited target-writer feedback."""

import argparse
from hashlib import sha256
from importlib.util import module_from_spec, spec_from_file_location
from itertools import combinations
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent.parent
PRIOR = HERE.parent / "draft-aware-composition"
ANCHOR = RUNS / "humanitarian-2664-admission/anchors.json"
NATIVE_2664 = RUNS / "humanitarian-2664-admission/source-preserving/scores.json"
BUDGETS = (1, 2, 4)


def load_prior():
    spec = spec_from_file_location("paired_draft_admission", PRIOR / "admission.py")
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


prior = load_prior()


def plan():
    paths = (Path(__file__), HERE / "protocol.md", PRIOR / "admission.py", PRIOR / "plan.json",
             ANCHOR, NATIVE_2664)
    assert prior.plan() == prior.load(PRIOR / "plan.json")
    return {"budgets": list(BUDGETS), "margin": prior.MARGIN,
            "sha256": {str(p.relative_to(RUNS)): sha256(p.read_bytes()).hexdigest() for p in paths}}


def humanitarian_rows():
    archive = prior.load(NATIVE_2664)["cases"]
    anchors = prior.load(ANCHOR)
    for key, row in archive.items():
        brief = row["brief"]
        assert row["abstained"] == (row["comparison"] == "NONE")
        fallback = brief if row["abstained"] else brief.removesuffix(" " + row["comparison"])
        expected = {"safeguards": "without-india", "india": "without-safeguards"}.get(key, "literal")
        expected_text = anchors[expected]["packet"]["answer"]
        if key == "none":
            assert expected_text.startswith(fallback + " ")
        else:
            assert expected_text == fallback
        assert row["abstained"] or fallback + " " + row["comparison"] == brief
        yield prior.Draft("2664", "append", key, fallback, brief, row["standalone"], row["require_both"])


def panels():
    groups = {
        "2553": list(prior.reform_rows()),
        "2664": list(humanitarian_rows()),
        "2721": list(prior.afghanistan_rows()),
        "2686": list(prior.mask_rows("2686", prior.TOLERANCE, "verbatim", {"scoped": "scoped"})),
        "2475": list(prior.mask_rows("2475", prior.DISABILITY, "authored/none", {
            "plain": "authored/plain", "scope": "authored/scope",
        })),
    }
    assert sum(map(len, groups.values())) == 74
    return groups


def summarize(row_gain, mass):
    choice, delta = row_gain
    return np.array([mass @ (choice * delta), mass @ (choice & (delta > 0)),
                     mass @ (choice & (delta < 0))])


def evaluate_panel(rows, prediction):
    count = len(rows)
    delta = np.array([r.delta for r in rows])
    mass = np.full(count, 1 / count)
    baseline = sum(r.baseline for r in rows) / count
    copy = np.array([r.native == r.fallback for r in rows])
    # Use the already verified fallback whenever the bytes are identical.
    eligible = np.flatnonzero(~copy).tolist()
    ranking = sorted(eligible, key=lambda i: (-prediction[i], rows[i].context))
    positive = delta > prior.MARGIN
    assert np.all(delta[copy] <= 0)

    def result(vector, labels):
        gain, improved, harmful = vector.tolist()
        return {"release": round(baseline + gain, 8), "gain": round(gain, 8),
                "improved_fraction": round(improved, 8), "harmful_fraction": round(harmful, 8),
                "labels": labels}

    def record(choice, labels=0):
        return result(summarize((choice, delta), mass), labels)

    audit_results = {}
    for capacity in BUDGETS:
        budget = min(len(eligible), capacity)
        selections = tuple(combinations(eligible, budget))
        direct_outcomes, broad_outcomes = [], []
        for indices in selections:
            seen = np.isin(np.arange(count), indices)
            direct = seen & positive
            deploy_widely = budget > 0 and delta[seen].mean() > prior.MARGIN
            broad = direct | (deploy_widely & ~seen & ~copy)
            direct_outcomes.append(summarize((direct, delta), mass))
            broad_outcomes.append(summarize((broad, delta), mass))
        ranked = np.isin(np.arange(count), ranking[:budget]) & positive
        audit_results[str(capacity)] = {
            "uniform_direct": result(np.mean(direct_outcomes, axis=0), budget),
            "ranked_direct": record(ranked, budget),
            "uniform_writer_gate": result(np.mean(broad_outcomes, axis=0), budget),
            "uniform_audit_subsets": len(selections),
        }
    return {
        "candidates": count, "eligible": len(eligible),
        "improved": int(sum(delta > 0)), "harmful": int(sum(delta < 0)),
        "baseline": round(baseline, 8),
        "controls": {
            "fallback": record(np.zeros(count, dtype=bool)),
            "always_native": record(~copy),
            "zero_shot_ridge": record((prediction > prior.MARGIN) & ~copy),
            "oracle": record(positive),
        },
        "audit": audit_results,
        "rank": [{"context": rows[i].context, "predicted_delta": round(float(prediction[i]), 8),
                  "release_delta": int(delta[i])} for i in ranking],
    }


def run():
    assert plan() == prior.load(HERE / "plan.json")
    groups = panels()
    output = {}
    for docket, held in groups.items():
        train = [r for key, rows in groups.items() if key != docket for r in rows]
        writers = {}
        for writer in sorted({r.writer for r in held}):
            rows = [r for r in held if r.writer == writer]
            prediction = prior.predict(train, rows, draft_aware=True)
            writers[writer] = evaluate_panel(rows, prediction)
        output[docket] = {"training_rows": len(train),
                          "training_improved": sum(r.delta > 0 for r in train),
                          "writers": writers}
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true")
    args = parser.parse_args()
    print(json.dumps(plan() if args.plan else run(), indent=2))
