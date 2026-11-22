"""Replay the fit without access to any target comparison labels."""
from collections import Counter
import json
from pathlib import Path
from unittest.mock import patch

import extract
import fit_transfer as study


def run():
    current = study.read(study.HERE/"fit.json")
    spec = study.read(study.HERE/"train-plan.json")
    sources = {name: study.donor_payoff(name) for name in study.DONORS}
    raw = study.read

    def blinded(path):
        if path == study.PATHS["2417"]:
            case = raw(path)
            return {name: case[name] for name in ("public", "delegate", "clause")}
        if path == study.PATHS["stress"]:
            case = raw(path)
            return {name: case[name] for name in ("cards", "stress")}
        if path.is_relative_to(study.TARGET.parents[1]):
            raise AssertionError(f"target answer key accessed during fit: {path.name}")
        return raw(path)

    with patch.object(study, "read", blinded), patch.object(extract, "read", blinded):
        features = study.extract_features()
        fit = study.train_donor(spec, features, sources)
        estimates = study.estimated_bonuses(spec, features, fit["fit"])
        routes = study.make_routes(spec, estimates, study.core_2417())
    assert routes == current["routes"]
    assert estimates == current["estimated_bonuses"]

    receipt_counts = Counter()
    for name, trace in fit["trajectories"].items():
        lead, early, late, joint = sources[name]
        for entry in trace:
            e, d = entry["view"], entry["reply"]
            received_e, received_d = entry["first"], entry["back"]
            paired = received_e and received_d
            expected = joint[len(late)*e+d] if paired else (
                early[e] if received_e else late[d] if received_d else lead
            )
            assert expected == entry["released"]
            receipt_counts["paired" if paired else "partial_or_silent"] += 1
    assert sum(receipt_counts.values()) == 512
    target = raw(study.HERE/"results.json")
    assert target["reference"] == [30,42,42,42,40,40,70,52,52,70,52,52]
    return {"target_answer_key_removed_during_replay": True,
            "routes_verified": sum(len(s["routes"]) for r in routes.values() for s in r),
            "source_feature_pairs": len(features)//2, "donor_receipts": dict(receipt_counts)}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
