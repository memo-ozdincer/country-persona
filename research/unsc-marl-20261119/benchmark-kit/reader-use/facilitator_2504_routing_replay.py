"""Replay frozen policies with semantic card assignments held through renumbering."""
import argparse
from hashlib import sha256
from itertools import permutations
import json
from unittest.mock import patch

import numpy as np

import facilitator_2504_routing as study
import facilitator_measured_channel_fit as trained

fit, D = study.fit, study.fit.D


def mask_map(order):
    return np.array([sum(1 << (order[i] - 1) for i in range(1, 4) if m & (1 << (i - 1)))
                     for m in range(8)])


def run(matrix, weights):
    provenance = trained.read(study.case.EVIDENCE / "provenance.json")
    points = np.asarray(provenance["authored_receipt_ceilings"])
    assert not any(row["score_bank"] == points.tolist() for row in weights["training_cases"].values())
    contexts = {}
    for name in fit.live.PRIORS:
        prior = fit.ROUTE.TEST_PRIORS[name]
        contexts[name] = (prior, *fit.context(points, prior))
    result = {}
    for order in ((0, *p) for p in permutations(range(1, 4))):
        masks = mask_map(order)
        inverse = np.argsort(order)
        relabeled = points[masks]
        channel = matrix[np.ix_(order, order)]

        def fixed_context(public, prior):
            assert np.array_equal(public, relabeled)
            original, opener, opening = next(row for row in contexts.values() if np.array_equal(row[0], prior))
            assert np.allclose(original[np.ix_(masks, masks)], prior, atol=1e-12, rtol=0)
            mapped_opener = tuple(inverse[a[masks]] for a in opener)
            mapped_mass = opening[np.ix_(masks, order, masks)]
            independently_rebuilt = np.einsum("lr,la,rb,abm->rbm", prior,
                                               *(D.one_hot(a) for a in mapped_opener), D.FIRST)
            assert np.allclose(independently_rebuilt, mapped_mass, atol=1e-12, rtol=0)
            return mapped_opener, mapped_mass

        with patch.object(trained.rubric, "ceilings", lambda _: relabeled.tolist()), patch.object(fit, "context", fixed_context):
            evaluation = trained.evaluate(weights, channel)
        for name, rows in evaluation["policies"].items():
            independent = rows["exact_held_independent"]["net"]
            for row in rows.values():
                row["gain_over_hindsight_no_request"] = row["net"] - independent
            if result:
                canonical = result["123"]["policies"][name]
                for option in ("exact_held_joint", "exact_held_independent"):
                    assert abs(rows[option]["net"] - canonical[option]["net"]) < 1e-10
        result["".join(map(str, order[1:]))] = evaluation
    return {"new_label_to_original_by_key": result}


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    replies = study.EVIDENCE / "admission.json"
    saved = study.archive.EVIDENCE / "fits.json"
    output = run(np.asarray(trained.read(replies)["matrix"]), trained.read(saved))
    output["sha256"] = {str(p.relative_to(study.HERE)): sha256(p.read_bytes()).hexdigest()
                        for p in (replies, saved, study.case.PACKET)}
    print(json.dumps(output, indent=2))
