"""Retain approved earlier claims even when the prior renderer did not print them."""
import argparse
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

import facilitator_claim_requests_score as initial

study = initial.study


def cover_prior_witnesses():
    previous = json.loads(study.PAIR_SCORE.read_text())
    views = previous["reassembled"]["views"]
    old = study.claims.EVIDENCE
    approved = json.loads((old / "marks.json").read_text())
    selected_views = {case[1] for case in study.TARGET.values()}
    additions = {}
    for key, entry in study.claims.items(study.claims.old_rows()).items():
        if approved[key]["supported"] != "met":
            continue
        claim = key.split("/")[1]
        for view in selected_views.intersection(entry["views"]):
            used = views[view]["reviewed"]["used_claims"]
            if claim not in used:
                used.append(claim)
                additions.setdefault(view, {})[claim] = {
                    "source": entry["source_id"], "witness": approved[key]["span"],
                }
    return previous, additions


def run(rows, marks):
    previous, additions = cover_prior_witnesses()
    baseline = initial.run(rows, marks)
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "approved.json"
        path.write_text(json.dumps(previous))
        with patch.object(study, "PAIR_SCORE", path):
            final = initial.run(rows, marks)
    for key, row in baseline["cases"].items():
        assert final["cases"][key]["original_release_points"] == row["original_release_points"]
        assert final["cases"][key]["record"]["release_points"] >= row["record"]["release_points"]
    return {"scope": "Scoring correction for approved but previously unprinted claims. "
                     "Input generation and claim reviews are unchanged.",
            "previously_approved_claims_restored": additions, "reassembled": final,
            "printed_only_scores": {k: v["record"]["release_points"] for k, v in baseline["cases"].items()}}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("directory", type=Path)
    p.add_argument("--marks", required=True, type=Path)
    args = p.parse_args()
    print(json.dumps(run(study.verify(args.directory), json.loads(args.marks.read_text())),
                     indent=2, ensure_ascii=False))
