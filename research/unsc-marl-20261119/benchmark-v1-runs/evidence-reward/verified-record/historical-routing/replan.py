"""Recompute the exact continuation under the published final-record score."""
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np

import historical as h

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(h.ARCHIVE.parent))
import facilitator_silence_joint_fit as study

D, fit, joint, routed = study.D, study.fit, study.joint, study.R


def run():
    score_path = HERE / "results.json"
    reviewed = h.e.read(score_path)["records"]
    earlier = h.e.read(h.ARCHIVE / "forecast.json")["budgets"]["70"]["laws"]
    scores = h.e.read(score_path)["expected"]
    report = {}
    for endpoint in ("v1.2", "compact"):
        public = np.array([reviewed[f"{endpoint}/{mask}"]["released_70"] for mask in range(8)])
        rows = {}
        for label, prior in routed.TEST_PRIORS.items():
            left, right = (np.array(row) for row in earlier[label]["openers"])
            mass = joint.opening(left, right, prior)
            values = {}
            for name, silence in (("exact_no_request", True), ("exact_continuation", False)):
                question, reply = fit.exact(public, mass, fit.PERFECT, independent=silence)
                team = (left, right, question, reply)
                values[name] = joint.metric(team, prior, public, fit.PERFECT)
            seen = scores[label]["native_compiled_v1.2" if endpoint == "v1.2" else "compact_v1.2"]
            for seen_key in ("learned", "fixed_1", "fixed_2", "fixed_3", "excerpt_planner"):
                assert seen[seen_key]["net"] <= values["exact_continuation"]["net"] + 1e-10
            rows[label] = {"net": {name: result["net"] for name, result in values.items()} | {
                name: seen[name]["net"] for name in ("learned", "fixed_1", "fixed_2", "fixed_3", "excerpt_planner")},
                "exact_gain_over_no_request": values["exact_continuation"]["net"] - values["exact_no_request"]["net"]}
        report[endpoint] = rows
    pins = (Path(__file__), HERE / "replan-protocol.md", score_path, h.ARCHIVE / "forecast.json",
            Path(study.__file__), Path(fit.__file__))
    return {"comparison": report, "sha256": {p.name: sha256(p.read_bytes()).hexdigest() for p in pins}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
