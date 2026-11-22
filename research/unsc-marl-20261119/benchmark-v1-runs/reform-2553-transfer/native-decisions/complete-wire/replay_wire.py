"""Map wire likelihoods to stable card choices and replay the frozen score tables."""
import json
from pathlib import Path
from unittest.mock import patch

from wire_decisions import HERE, PARENT, READ, prior, frozen
import score_native as original


def convert(raw, measure):
    report = {}
    for key, value in raw.items():
        alternatives = value["candidate_scores"]["alternatives"]
        mass = {item["ids"][0]: item[measure] for item in alternatives}
        scores = {"A": mass["1"], "B": mass["2"]}
        label = max(scores, key=scores.get)
        expected = "selected" if measure == "log_mass" else "canonical_only"
        assert json.loads(value["candidate_scores"][expected]) == ["1" if label == "A" else "2"]
        report[key] = {"label": label, "logits": scores}
    return report


def run():
    output = READ(HERE / "verified.json")["outputs"]
    current = {key: value for key, value in output.items() if not key.startswith("forecast/")}
    altered = current | {key.removeprefix("forecast/"): value for key, value in output.items()
                         if key.startswith("forecast/")}
    earlier = READ(PARENT / "scores.json")
    frozen_target = PARENT / "verified.json"
    outcomes = {}
    for mode, data, measure in (("wire", current, "log_mass"),
                                ("canonical", current, "canonical_logp"),
                                ("forecast", altered, "log_mass")):
        rows = convert(data, measure)

        def expose(path):
            if Path(path) == frozen_target:
                return {"outputs": rows}
            return READ(path)

        with patch.object(original, "READ", expose):
            scores = original.run()
        scores["sha256"].pop("verified.json")
        for a, b in zip(scores["scenarios"], earlier["scenarios"], strict=True):
            assert (a["order"], a["receipt"]) == (b["order"], b["receipt"])
            for view in original.MODES:
                assert all(a["results"][view][key] == b["results"][view][key]
                           for key in ("prior_fixed", "prior_learned", "prior_oracle"))
        outcomes[mode] = scores
    for a, b in zip(outcomes["wire"]["scenarios"], outcomes["forecast"]["scenarios"], strict=True):
        if (a["order"], a["receipt"]) != ("uk_later", .95):
            assert a["results"] == b["results"]
    total = sum(row["independent_dispatch_checks"] for row in outcomes.values())
    return {"modes": outcomes, "atomic_reference": {
                "mean_rewards": earlier["means"], "label_order_agreements": earlier["label_order_agreements"]},
            "dispatch_checks": total,
            "sha256": {str(p.relative_to(prior.STUDY)): prior.digest(p) for p in (
                Path(__file__), HERE / "plan.json", HERE / "verified.json", PARENT / "scores.json",
                PARENT / "score_native.py")}}


if __name__ == "__main__":
    frozen.emit(run())
