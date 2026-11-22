"""Re-score the matched records after replacing only the UK generation."""
import json
from unittest.mock import patch

import numpy as np

import myanmar_protected_transfer as transfer
import myanmar_sponsorship_probe as probe
import source_request_policy as routing
from source_record_run import digest


def review():
    path = probe.TARGET / "annotation.json"
    mark = json.loads(path.read_text())
    assert mark["transcript_sha256"] == digest(probe.TARGET / "transcript.jsonl")
    before, labels = transfer.annotation_rows(probe.ORIGINAL)
    after = {**before, "uk": probe.replay(probe.TARGET)}
    updated = {**labels, "components": {**labels["components"], "uk": mark["component"]}}
    baseline = json.loads((probe.ORIGINAL / "score.json").read_text())
    plans_dir = probe.TARGET.parent / "myanmar-public-rubric-fit"
    plans = json.loads((plans_dir / "fit.json").read_text())
    assert json.loads((plans_dir / "launch.json").read_text())["evaluation_sha256"] == digest(
        probe.ORIGINAL / "score.json")
    with patch.object(transfer, "annotation_rows", return_value=(after, updated)):
        report = transfer.run(probe.ORIGINAL, exact=True)
    report["replacement_annotation_sha256"] = digest(path)
    report["scope"] = "Matched UK sponsorship prompt change. All other generated text and routing policies are reused."
    old_points = np.array([r["points"] for r in baseline["records"]])
    new_points = np.array([r["points"] for r in report["records"]])
    for old, new in zip(baseline["records"], report["records"], strict=True):
        if not old["mask"] & 1:
            assert old == new
    report["original_points"] = old_points.tolist()
    report["revised_points"] = new_points.tolist()
    for name, prior in routing.TEST_PRIORS.items():
        case = report["priors"][name]
        for key in ("learned_policy", "exact_planner_policy"):
            policy = list(map(np.asarray, plans[key]))
            case[key] = routing.evaluate(policy, prior, new_points, transfer.DELIVERY_LOSS)
            assert case[key]["net"] <= case["exact_optional"]["net"] + 1e-9
            if key == "learned_policy":
                case["learned_request_erased"] = routing.evaluate(
                    policy, prior, new_points, transfer.DELIVERY_LOSS, force_missing=True)
    return report


if __name__ == "__main__":
    print(json.dumps(review(), indent=2, ensure_ascii=False))
