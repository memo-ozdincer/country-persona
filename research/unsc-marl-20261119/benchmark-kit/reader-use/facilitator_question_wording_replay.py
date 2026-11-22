"""Reweight the frozen routing comparison under measured prompt variants."""
import argparse
from hashlib import sha256
import json

import numpy as np

import facilitator_measured_channel_fit as trained
import facilitator_question_wording as study


def replay(original, variants, weights):
    old = np.asarray(original["matrix"])
    fresh = np.asarray(variants["matrix"])
    assert old.shape == fresh.shape == (4, 4)
    scenarios = {"archived": old}
    for i in range(2):
        alternative = old.copy()
        alternative[0] = fresh[i]
        scenarios[f"generic_{i + 1}_only"] = alternative.copy()
        for c in range(1, 4):
            alternative[c, c] = fresh[i + 2, c]
        scenarios[f"paired_{i + 1}"] = alternative
    results = {}
    for name, matrix in scenarios.items():
        trial = trained.evaluate(weights, matrix)
        for label, arms in trial["policies"].items():
            oracle_quiet = arms["exact_held_independent"]["net"]
            for row in arms.values():
                row["gain_over_hindsight_no_request"] = row["net"] - oracle_quiet
            if name != "archived":
                initial = results["archived"]["policies"][label]
                for key in ("ideal_fit", "measured_fit", "measured_independent", "ideal_exact"):
                    assert arms[key]["policy"] == initial[key]["policy"]
        results[name] = trial
    return {"replays": results, "passing_variants_by_card": {
        str(c): {"generic": int(fresh[:2, c].sum()), "matched": int(fresh[2:, c].sum())} for c in range(1, 4)
    }}


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    files = (study.archive.EVIDENCE / "admission.json", study.EVIDENCE / "admission.json",
             study.archive.EVIDENCE / "fits.json")
    output = replay(*(trained.read(f) for f in files))
    output["sha256"] = {str(f.relative_to(study.HERE)): sha256(f.read_bytes()).hexdigest() for f in files}
    print(json.dumps(output, indent=2))
